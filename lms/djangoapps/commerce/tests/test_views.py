""" Tests for commerce views. """

from nose.plugins.attrib import attr

import ddt
import json
from django.core.urlresolvers import reverse
from django.test import TestCase
import mock

from student.tests.factories import UserFactory
from openedx.core.djangoapps.theming.tests.test_util import with_comprehensive_theme
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from student.models import CourseEnrollment
from course_modes.models import CourseMode


class UserMixin(object):
    """ Mixin for tests involving users. """

    def setUp(self):
        super(UserMixin, self).setUp()
        self.user = UserFactory()

    def _login(self):
        """ Log into LMS. """
        self.client.login(username=self.user.username, password='test')


@attr('shard_1')
@ddt.ddt
class ReceiptViewTests(UserMixin, ModuleStoreTestCase):
    """ Tests for the receipt view. """

    def setUp(self):
        """
        Add a user and a course
        """
        super(ReceiptViewTests, self).setUp()
        self.user = UserFactory()
        self.client.login(username=self.user.username, password='test')
        self.course = CourseFactory.create(
            org='edX',
            course='900',
            run='test_run'
        )

    def test_login_required(self):
        """ The view should redirect to the login page if the user is not logged in. """
        self.client.logout()
        response = self.client.post(reverse('commerce:checkout_receipt'))
        self.assertEqual(response.status_code, 302)

    def post_to_receipt_page(self, post_data):
        """ DRY helper """
        response = self.client.post(reverse('commerce:checkout_receipt'), params={'basket_id': 1}, data=post_data)
        self.assertEqual(response.status_code, 200)
        return response

    def test_user_verification_status_success(self):
        """
        Test user verification status. If the user enrollment for the course belongs to verified modes
        e.g. Verified, Professional then verification is required.
        """
        # Enroll as verified in the course with the current user.
        CourseEnrollment.enroll(self.user, self.course.id, mode=CourseMode.VERIFIED)
        response = self.client.get(reverse('commerce:user_verification_status'), data={'course_id': self.course.id})
        json_data = json.loads(response.content)
        self.assertEqual(json_data['is_verification_required'], True)

        # Enroll as honor in the course with the current user.
        CourseEnrollment.enroll(self.user, self.course.id, mode=CourseMode.HONOR)
        response = self.client.get(reverse('commerce:user_verification_status'), data={'course_id': self.course.id})
        json_data = json.loads(response.content)
        self.assertEqual(json_data['is_verification_required'], False)

    def test_user_verification_status_failure(self):
        """
        Test user verification status failure. View should required HttpResponseBadRequest 400 if course id is missing.
        """
        response = self.client.get(reverse('commerce:user_verification_status'))
        self.assertEqual(response.status_code, 400)

    @ddt.data('decision', 'reason_code', 'signed_field_names', None)
    def test_is_cybersource(self, post_key):
        """
        Ensure the view uses three specific POST keys to detect a request initiated by Cybersource.
        """
        self._login()
        post_data = {'decision': 'REJECT', 'reason_code': '200', 'signed_field_names': 'dummy'}
        if post_key is not None:
            # a key will be missing; we will not expect the receipt page to handle a cybersource decision
            del post_data[post_key]
            expected_pattern = r"<title>(\s+)Receipt"
        else:
            expected_pattern = r"<title>(\s+)Payment Failed"
        response = self.post_to_receipt_page(post_data)
        self.assertRegexpMatches(response.content, expected_pattern)

    @ddt.data('ACCEPT', 'REJECT', 'ERROR')
    def test_cybersource_decision(self, decision):
        """
        Ensure the view renders a page appropriately depending on the Cybersource decision.
        """
        self._login()
        post_data = {'decision': decision, 'reason_code': '200', 'signed_field_names': 'dummy'}
        expected_pattern = r"<title>(\s+)Receipt" if decision == 'ACCEPT' else r"<title>(\s+)Payment Failed"
        response = self.post_to_receipt_page(post_data)
        self.assertRegexpMatches(response.content, expected_pattern)

    @ddt.data(True, False)
    @mock.patch('commerce.views.is_user_payment_error')
    def test_cybersource_message(self, is_user_message_expected, mock_is_user_payment_error):
        """
        Ensure that the page displays the right message for the reason_code (it
        may be a user error message or a system error message).
        """
        mock_is_user_payment_error.return_value = is_user_message_expected
        self._login()
        response = self.post_to_receipt_page({'decision': 'REJECT', 'reason_code': '99', 'signed_field_names': 'dummy'})
        self.assertTrue(mock_is_user_payment_error.called)
        self.assertTrue(mock_is_user_payment_error.call_args[0][0], '99')

        user_message = "There was a problem with this transaction"
        system_message = "A system error occurred while processing your payment"
        self.assertRegexpMatches(response.content, user_message if is_user_message_expected else system_message)
        self.assertNotRegexpMatches(response.content, user_message if not is_user_message_expected else system_message)

    @with_comprehensive_theme("edx.org")
    def test_hide_nav_header(self):
        self._login()
        post_data = {'decision': 'ACCEPT', 'reason_code': '200', 'signed_field_names': 'dummy'}
        response = self.post_to_receipt_page(post_data)

        # Verify that the header navigation links are hidden for the edx.org version
        self.assertNotContains(response, "How it Works")
        self.assertNotContains(response, "Find courses")
        self.assertNotContains(response, "Schools & Partners")
