""" Tests for commerce views. """

import json
from uuid import uuid4

from ddt import ddt, data
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
import httpretty
from httpretty.core import HTTPrettyRequestEmpty
import jwt
from requests import Timeout
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from commerce.constants import OrderStatus, Messages
from course_modes.models import CourseMode
from enrollment.api import add_enrollment
from student.models import CourseEnrollment
from student.tests.factories import UserFactory, CourseModeFactory


ECOMMERCE_API_URL = 'http://example.com/api'
ECOMMERCE_API_SIGNING_KEY = 'edx'
ORDER_NUMBER = "100004"
ECOMMERCE_API_SUCCESSFUL_BODY = json.dumps({'status': OrderStatus.COMPLETE, 'number': ORDER_NUMBER})


@ddt
@override_settings(ECOMMERCE_API_URL=ECOMMERCE_API_URL, ECOMMERCE_API_SIGNING_KEY=ECOMMERCE_API_SIGNING_KEY)
class OrdersViewTests(ModuleStoreTestCase):
    """
    Tests for the commerce orders view.
    """

    def _login(self):
        """ Log into LMS. """
        self.client.login(username=self.user.username, password='test')

    def _post_to_view(self, course_id=None):
        """
        POST to the view being tested.

        Arguments
            course_id (str) --  ID of course for which a seat should be ordered.

        :return: Response
        """
        course_id = unicode(course_id or self.course.id)
        return self.client.post(self.url, {'course_id': course_id})

    def _mock_ecommerce_api(self, status=200, body=None):
        """
        Mock calls to the E-Commerce API.

        The calling test should be decorated with @httpretty.activate.
        """
        self.assertTrue(httpretty.is_enabled(), 'Test is missing @httpretty.activate decorator.')

        url = ECOMMERCE_API_URL + '/orders/'
        body = body or ECOMMERCE_API_SUCCESSFUL_BODY
        httpretty.register_uri(httpretty.POST, url, status=status, body=body)

    def assertResponseMessage(self, response, expected_msg):
        """ Asserts the detail field in the response's JSON body equals the expected message. """
        actual = json.loads(response.content)['detail']
        self.assertEqual(actual, expected_msg)

    def assertValidEcommerceApiErrorResponse(self, response):
        """ Asserts the response is a valid response sent when the E-Commerce API is unavailable. """
        self.assertEqual(response.status_code, 503)
        self.assertResponseMessage(response, 'Call to E-Commerce API failed. Order creation failed.')

    def setUp(self):
        super(OrdersViewTests, self).setUp()
        self.url = reverse('commerce:orders')
        self.user = UserFactory()
        self._login()

        self.course = CourseFactory.create()

        # TODO Verify this is the best method to create CourseMode objects.
        # TODO Find/create constants for the modes.
        for mode in ['honor', 'verified', 'audit']:
            CourseModeFactory.create(
                course_id=self.course.id,
                mode_slug=mode,
                mode_display_name=mode,
                sku=uuid4().hex.decode('ascii')
            )

    def test_login_required(self):
        """
        The view should return HTTP 403 status if the user is not logged in.
        """
        self.client.logout()
        self.assertEqual(403, self._post_to_view().status_code)

    @data('delete', 'get', 'put')
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

    @httpretty.activate
    @data(400, 401, 405, 406, 429, 500, 503)
    def test_ecommerce_api_bad_status(self, status):
        """
        If the E-Commerce API returns an HTTP status not equal to 200, the view should log an error and return
        an HTTP 503 status.
        """
        self._mock_ecommerce_api(status=status, body=json.dumps({'user_message': 'FAIL!'}))
        response = self._post_to_view()
        self.assertValidEcommerceApiErrorResponse(response)
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course.id))

    @httpretty.activate
    def test_ecommerce_api_timeout(self):
        """
        If the call to the E-Commerce API times out, the view should log an error and return an HTTP 503 status.
        """
        # Verify that the view responds appropriately if calls to the E-Commerce API timeout.
        def request_callback(_request, _uri, _headers):
            """ Simulates API timeout """
            raise Timeout

        self._mock_ecommerce_api(body=request_callback)
        response = self._post_to_view()
        self.assertValidEcommerceApiErrorResponse(response)
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course.id))

    @httpretty.activate
    def test_ecommerce_api_bad_data(self):
        """
        If the E-Commerce API returns data that is not JSON, the view should return an HTTP 503 status.
        """
        self._mock_ecommerce_api(body='TOTALLY NOT JSON!')
        response = self._post_to_view()
        self.assertValidEcommerceApiErrorResponse(response)
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course.id))

    @data(True, False)
    @httpretty.activate
    def test_course_with_honor_seat_sku(self, user_is_active):
        """
        If the course has a SKU, the view should get authorization from the E-Commerce API before enrolling
        the user in the course. If authorization is approved, the user should be redirected to the user dashboard.
        """

        # Set user's active flag
        self.user.is_active = user_is_active
        self.user.save()  # pylint: disable=no-member

        def request_callback(_method, _uri, headers):
            """ Mock the E-Commerce API's call to the enrollment API. """
            add_enrollment(self.user.username, unicode(self.course.id), 'honor')
            return 200, headers, ECOMMERCE_API_SUCCESSFUL_BODY

        self._mock_ecommerce_api(body=request_callback)
        response = self._post_to_view()

        # Validate the response content
        msg = Messages.ORDER_COMPLETED.format(order_number=ORDER_NUMBER)
        self.assertResponseMessage(response, msg)

        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course.id))

        # Verify the correct information was passed to the E-Commerce API
        request = httpretty.last_request()
        sku = CourseMode.objects.filter(course_id=self.course.id, mode_slug='honor', sku__isnull=False)[0].sku
        self.assertEqual(request.body, '{{"sku": "{}"}}'.format(sku))
        self.assertEqual(request.headers['Content-Type'], 'application/json')

        # Verify the JWT is correct
        expected_jwt = jwt.encode({'username': self.user.username, 'email': self.user.email},
                                  ECOMMERCE_API_SIGNING_KEY)
        self.assertEqual(request.headers['Authorization'], 'JWT {}'.format(expected_jwt))

    @httpretty.activate
    def test_order_not_complete(self):
        self._mock_ecommerce_api(body=json.dumps({'status': OrderStatus.OPEN, 'number': ORDER_NUMBER}))
        response = self._post_to_view()
        self.assertEqual(response.status_code, 202)
        msg = Messages.ORDER_INCOMPLETE_ENROLLED.format(order_number=ORDER_NUMBER)
        self.assertResponseMessage(response, msg)

        # TODO Eventually we should NOT be enrolling users directly from this view.
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course.id))

    def _test_course_without_sku(self):
        """
        Validates the view bypasses the E-Commerce API when the course has no CourseModes with SKUs.
        """
        # Place an order
        self._mock_ecommerce_api()
        response = self._post_to_view()

        # Validate the response content
        self.assertEqual(response.status_code, 200)
        msg = Messages.NO_SKU_ENROLLED.format(enrollment_mode='honor', course_id=self.course.id,
                                              username=self.user.username)
        self.assertResponseMessage(response, msg)

        # The user should be enrolled, and no calls made to the E-Commerce API
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course.id))
        self.assertIsInstance(httpretty.last_request(), HTTPrettyRequestEmpty)

    @httpretty.activate
    def test_course_without_sku(self):
        """
        If the course does NOT have a SKU, the user should be enrolled in the course (under the honor mode) and
        redirected to the user dashboard.
        """
        # Remove SKU from all course modes
        for course_mode in CourseMode.objects.filter(course_id=self.course.id):
            course_mode.sku = None
            course_mode.save()

        self._test_course_without_sku()

    @httpretty.activate
    @override_settings(ECOMMERCE_API_URL=None, ECOMMERCE_API_SIGNING_KEY=None)
    def test_no_settings(self):
        """
        If no settings exist to define the E-Commerce API URL or signing key, the view should enroll the user.
        """
        response = self._post_to_view()

        # Validate the response
        self._mock_ecommerce_api()
        self.assertEqual(response.status_code, 200)
        msg = Messages.NO_ECOM_API.format(username=self.user.username, course_id=self.course.id)
        self.assertResponseMessage(response, msg)

        # Ensure that the user is not enrolled and that no calls were made to the E-Commerce API
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course.id))
        self.assertIsInstance(httpretty.last_request(), HTTPrettyRequestEmpty)

    @httpretty.activate
    def test_empty_sku(self):
        """ If the CourseMode has an empty string for a SKU, the API should not be used. """
        # Set SKU to empty string for all modes.
        for course_mode in CourseMode.objects.filter(course_id=self.course.id):
            course_mode.sku = ''
            course_mode.save()

        self._test_course_without_sku()
