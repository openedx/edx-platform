""" Commerce API v0 view tests. """
from datetime import datetime, timedelta
import json
import itertools
from uuid import uuid4
import httpretty

import ddt
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings
import mock
from nose.plugins.attrib import attr
import pytz
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from commerce.constants import Messages
from commerce.tests import TEST_BASKET_ID, TEST_ORDER_NUMBER, TEST_PAYMENT_DATA, TEST_API_URL, TEST_API_SIGNING_KEY
from commerce.tests.mocks import mock_basket_order, mock_create_basket
from commerce.tests.test_views import UserMixin
from course_modes.models import CourseMode
from edx_rest_api_client import exceptions
from embargo.test_utils import restrict_course
from enrollment.api import get_enrollment
from openedx.core.lib.django_test_client_utils import get_absolute_url
from student.models import CourseEnrollment
from student.tests.factories import CourseModeFactory
from student.tests.tests import EnrollmentEventTestMixin
from xmodule.modulestore.django import modulestore
from commerce.api.v0.views import SAILTHRU_CAMPAIGN_COOKIE


@attr(shard=1)
@ddt.ddt
@override_settings(ECOMMERCE_API_URL=TEST_API_URL, ECOMMERCE_API_SIGNING_KEY=TEST_API_SIGNING_KEY)
class BasketsViewTests(EnrollmentEventTestMixin, UserMixin, ModuleStoreTestCase):
    """
    Tests for the commerce orders view.
    """
    def _post_to_view(self, course_id=None, marketing_email_opt_in=False):
        """
        POST to the view being tested.

        Arguments
            course_id (str) --  ID of course for which a seat should be ordered.

        :return: Response
        """
        payload = {
            "course_id": unicode(course_id or self.course.id)
        }
        if marketing_email_opt_in:
            payload["email_opt_in"] = True

        self.client.cookies[SAILTHRU_CAMPAIGN_COOKIE] = 'sailthru id'
        return self.client.post(self.url, payload)

    def assertResponseMessage(self, response, expected_msg):
        """ Asserts the detail field in the response's JSON body equals the expected message. """
        actual = json.loads(response.content)['detail']
        self.assertEqual(actual, expected_msg)

    def assertResponsePaymentData(self, response):
        """ Asserts correctness of a JSON body containing payment information. """
        actual_response = json.loads(response.content)
        self.assertEqual(actual_response, TEST_PAYMENT_DATA)

    def assertValidEcommerceInternalRequestErrorResponse(self, response):
        """ Asserts the response is a valid response sent when the E-Commerce API is unavailable. """
        self.assertEqual(response.status_code, 500)
        actual = json.loads(response.content)['detail']
        self.assertIn('Call to E-Commerce API failed', actual)

    def assertUserNotEnrolled(self):
        """ Asserts that the user is NOT enrolled in the course, and that an enrollment event was NOT fired. """
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course.id))
        self.assert_no_events_were_emitted()

    def setUp(self):
        super(BasketsViewTests, self).setUp()
        self.url = reverse('commerce_api:v0:baskets:create')
        self._login()

        self.course = CourseFactory.create()

        # TODO Verify this is the best method to create CourseMode objects.
        # TODO Find/create constants for the modes.
        for mode in [CourseMode.HONOR, CourseMode.VERIFIED, CourseMode.AUDIT]:
            sku_string = uuid4().hex.decode('ascii')
            CourseModeFactory.create(
                course_id=self.course.id,
                mode_slug=mode,
                mode_display_name=mode,
                sku=sku_string,
                bulk_sku='BULK-{}'.format(sku_string)
            )

        # Ignore events fired from UserFactory creation
        self.reset_tracker()

    @mock.patch.dict(settings.FEATURES, {'EMBARGO': True})
    def test_embargo_restriction(self):
        """
        The view should return HTTP 403 status if the course is embargoed.
        """
        with restrict_course(self.course.id) as redirect_url:
            response = self._post_to_view()
            self.assertEqual(403, response.status_code)
            body = json.loads(response.content)
            self.assertEqual(get_absolute_url(redirect_url), body['user_message_url'])

    def test_login_required(self):
        """
        The view should return HTTP 403 status if the user is not logged in.
        """
        self.client.logout()
        self.assertEqual(403, self._post_to_view().status_code)

    @ddt.data('delete', 'get', 'put')
    def test_post_required(self, method):
        """
        Verify that the view only responds to POST operations.
        """
        response = getattr(self.client, method)(self.url)
        self.assertEqual(405, response.status_code)

    def test_invalid_course(self):
        """
        If the course does not exist, the view should return HTTP 406.
        """
        # TODO Test inactive courses, and those not open for enrollment.
        self.assertEqual(406, self._post_to_view('aaa/bbb/ccc').status_code)

    def test_invalid_request_data(self):
        """
        If invalid data is supplied with the request, the view should return HTTP 406.
        """
        self.assertEqual(406, self.client.post(self.url, {}).status_code)
        self.assertEqual(406, self.client.post(self.url, {'not_course_id': ''}).status_code)

    def test_ecommerce_api_timeout(self):
        """
        If the call to the E-Commerce API times out, the view should log an error and return an HTTP 503 status.
        """
        with mock_create_basket(exception=exceptions.Timeout):
            response = self._post_to_view()

        self.assertValidEcommerceInternalRequestErrorResponse(response)
        self.assertUserNotEnrolled()

    def test_ecommerce_api_error(self):
        """
        If the E-Commerce API raises an error, the view should return an HTTP 503 status.
        """
        with mock_create_basket(exception=exceptions.SlumberBaseException):
            response = self._post_to_view()

        self.assertValidEcommerceInternalRequestErrorResponse(response)
        self.assertUserNotEnrolled()

    def _test_successful_ecommerce_api_call(self, is_completed=True):
        """
        Verifies that the view contacts the E-Commerce API with the correct data and headers.
        """
        with mock.patch('commerce.api.v0.views.audit_log') as mock_audit_log:
            response = self._post_to_view()

            # Verify that an audit message was logged
            self.assertTrue(mock_audit_log.called)

        # Validate the response content
        if is_completed:
            msg = Messages.ORDER_COMPLETED.format(order_number=TEST_ORDER_NUMBER)
            self.assertResponseMessage(response, msg)
        else:
            self.assertResponsePaymentData(response)

        # make sure ecommerce API call forwards Sailthru cookie
        self.assertIn('{}=sailthru id'.format(SAILTHRU_CAMPAIGN_COOKIE), httpretty.last_request().headers['cookie'])

    @ddt.data(True, False)
    def test_course_with_honor_seat_sku(self, user_is_active):
        """
        If the course has a SKU, the view should get authorization from the E-Commerce API before enrolling
        the user in the course. If authorization is approved, the user should be redirected to the user dashboard.
        """

        # Set user's active flag
        self.user.is_active = user_is_active
        self.user.save()  # pylint: disable=no-member

        return_value = {'id': TEST_BASKET_ID, 'payment_data': None, 'order': {'number': TEST_ORDER_NUMBER}}
        with mock_create_basket(response=return_value):
            self._test_successful_ecommerce_api_call()

    @ddt.data(True, False)
    def test_course_with_paid_seat_sku(self, user_is_active):
        """
        If the course has a SKU, the view should return data that the client
        will use to redirect the user to an external payment processor.
        """
        # Set user's active flag
        self.user.is_active = user_is_active
        self.user.save()  # pylint: disable=no-member

        return_value = {'id': TEST_BASKET_ID, 'payment_data': TEST_PAYMENT_DATA, 'order': None}
        with mock_create_basket(response=return_value):
            self._test_successful_ecommerce_api_call(False)

    def _test_course_without_sku(self, enrollment_mode=CourseMode.DEFAULT_MODE_SLUG):
        """
        Validates the view bypasses the E-Commerce API when the course has no CourseModes with SKUs.
        """
        # Place an order
        with mock_create_basket(expect_called=False):
            response = self._post_to_view()

        # Validate the response content
        self.assertEqual(response.status_code, 200)
        msg = Messages.NO_SKU_ENROLLED.format(
            enrollment_mode=enrollment_mode,
            course_id=self.course.id,
            username=self.user.username
        )
        self.assertResponseMessage(response, msg)

    def test_course_without_sku_default(self):
        """
        If the course does NOT have a SKU, the user should be enrolled in the course (under the default mode) and
        redirected to the user dashboard.
        """
        # Remove SKU from all course modes
        for course_mode in CourseMode.objects.filter(course_id=self.course.id):
            course_mode.sku = None
            course_mode.save()

        self._test_course_without_sku()

    def test_course_without_sku_honor(self):
        """
        If the course does not have an SKU and has an honor mode, the user
        should be enrolled as honor. This ensures backwards
        compatibility with courses existing before the removal of
        honor certificates.
        """
        # Remove all existing course modes
        CourseMode.objects.filter(course_id=self.course.id).delete()
        # Ensure that honor mode exists
        CourseMode(
            mode_slug=CourseMode.HONOR,
            mode_display_name="Honor Cert",
            course_id=self.course.id
        ).save()
        # We should be enrolled in honor mode
        self._test_course_without_sku(enrollment_mode=CourseMode.HONOR)

    @override_settings(ECOMMERCE_API_URL=None, ECOMMERCE_API_SIGNING_KEY=None)
    def test_ecommerce_service_not_configured(self):
        """
        If the E-Commerce Service is not configured, the view should enroll the user.
        """
        with mock_create_basket(expect_called=False):
            response = self._post_to_view()

        # Validate the response
        self.assertEqual(response.status_code, 200)
        msg = Messages.NO_ECOM_API.format(username=self.user.username, course_id=self.course.id)
        self.assertResponseMessage(response, msg)

        # Ensure that the user is not enrolled and that no calls were made to the E-Commerce API
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course.id))

    def assertProfessionalModeBypassed(self):
        """ Verifies that the view returns HTTP 406 when a course with no honor or audit mode is encountered. """

        CourseMode.objects.filter(course_id=self.course.id).delete()
        mode = CourseMode.NO_ID_PROFESSIONAL_MODE
        sku_string = uuid4().hex.decode('ascii')
        CourseModeFactory.create(course_id=self.course.id, mode_slug=mode, mode_display_name=mode,
                                 sku=sku_string, bulk_sku='BULK-{}'.format(sku_string))

        with mock_create_basket(expect_called=False):
            response = self._post_to_view()

        # The view should return an error status code
        self.assertEqual(response.status_code, 406)
        msg = Messages.NO_DEFAULT_ENROLLMENT_MODE.format(course_id=self.course.id)
        self.assertResponseMessage(response, msg)

    def test_course_with_professional_mode_only(self):
        """ Verifies that the view behaves appropriately when the course only has a professional mode. """
        self.assertProfessionalModeBypassed()

    @override_settings(ECOMMERCE_API_URL=None, ECOMMERCE_API_SIGNING_KEY=None)
    def test_professional_mode_only_and_ecommerce_service_not_configured(self):
        """
        Verifies that the view behaves appropriately when the course only has a professional mode and
        the E-Commerce Service is not configured.
        """
        self.assertProfessionalModeBypassed()

    def test_empty_sku(self):
        """ If the CourseMode has an empty string for a SKU, the API should not be used. """
        # Set SKU to empty string for all modes.
        for course_mode in CourseMode.objects.filter(course_id=self.course.id):
            course_mode.sku = ''
            course_mode.save()

        self._test_course_without_sku()

    def test_existing_active_enrollment(self):
        """ The view should respond with HTTP 409 if the user has an existing active enrollment for the course. """

        # Enroll user in the course
        CourseEnrollment.enroll(self.user, self.course.id)
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course.id))

        response = self._post_to_view()
        self.assertEqual(response.status_code, 409)
        msg = Messages.ENROLLMENT_EXISTS.format(username=self.user.username, course_id=self.course.id)
        self.assertResponseMessage(response, msg)

    def test_existing_inactive_enrollment(self):
        """
        If the user has an inactive enrollment for the course, the view should behave as if the
        user has no enrollment.
        """
        # Create an inactive enrollment
        CourseEnrollment.enroll(self.user, self.course.id)
        CourseEnrollment.unenroll(self.user, self.course.id, True)
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course.id))
        self.assertIsNotNone(get_enrollment(self.user.username, unicode(self.course.id)))

        with mock_create_basket():
            self._test_successful_ecommerce_api_call(False)

    @mock.patch('commerce.api.v0.views.update_email_opt_in')
    @ddt.data(*itertools.product((False, True), (False, True), (False, True)))
    @ddt.unpack
    def test_marketing_email_opt_in(self, is_opt_in, has_sku, is_exception, mock_update):
        """
        Ensures the email opt-in flag is handled, if present, and that problems handling the
        flag don't cause the rest of the enrollment transaction to fail.
        """
        if not has_sku:
            for course_mode in CourseMode.objects.filter(course_id=self.course.id):
                course_mode.sku = None
                course_mode.save()

        if is_exception:
            mock_update.side_effect = Exception("boink")

        return_value = {'id': TEST_BASKET_ID, 'payment_data': None, 'order': {'number': TEST_ORDER_NUMBER}}
        with mock_create_basket(response=return_value, expect_called=has_sku):
            response = self._post_to_view(marketing_email_opt_in=is_opt_in)
        self.assertEqual(mock_update.called, is_opt_in)
        self.assertEqual(response.status_code, 200)

    def test_closed_course(self):
        """
        Ensure that the view does not attempt to create a basket for closed
        courses.
        """
        self.course.enrollment_end = datetime.now(pytz.UTC) - timedelta(days=1)
        modulestore().update_item(self.course, self.user.id)  # pylint:disable=no-member
        with mock_create_basket(expect_called=False):
            self.assertEqual(self._post_to_view().status_code, 406)


@attr(shard=1)
@override_settings(ECOMMERCE_API_URL=TEST_API_URL, ECOMMERCE_API_SIGNING_KEY=TEST_API_SIGNING_KEY)
class BasketOrderViewTests(UserMixin, TestCase):
    """ Tests for the basket order view. """
    view_name = 'commerce_api:v0:baskets:retrieve_order'
    MOCK_ORDER = {'number': 1}
    path = reverse(view_name, kwargs={'basket_id': 1})

    def setUp(self):
        super(BasketOrderViewTests, self).setUp()
        self._login()

    def test_order_found(self):
        """ If the order is located, the view should pass the data from the API. """

        with mock_basket_order(basket_id=1, response=self.MOCK_ORDER):
            response = self.client.get(self.path)

        self.assertEqual(response.status_code, 200)
        actual = json.loads(response.content)
        self.assertEqual(actual, self.MOCK_ORDER)

    def test_order_not_found(self):
        """ If the order is not found, the view should return a 404. """
        with mock_basket_order(basket_id=1, exception=exceptions.HttpNotFoundError):
            response = self.client.get(self.path)
        self.assertEqual(response.status_code, 404)

    def test_login_required(self):
        """ The view should return 403 if the user is not logged in. """
        self.client.logout()
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 403)
