# coding=UTF-8
"""
Tests for signal handling in commerce djangoapp.
"""
from __future__ import unicode_literals

import base64
import json
from urlparse import urljoin

import ddt
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.test.utils import override_settings
import httpretty
import mock
from opaque_keys.edx.keys import CourseKey
from requests import Timeout

from student.models import UNENROLL_DONE
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from commerce.signals import (refund_seat, send_refund_notification, generate_refund_notification_body)
from commerce.tests import TEST_PUBLIC_URL_ROOT, TEST_API_URL, TEST_API_SIGNING_KEY, JSON
from commerce.tests.mocks import mock_create_refund
from course_modes.models import CourseMode

HELPDESK = 'Zendesk'
HELPDESK_URL = 'http://zendesk.example.com/'
HELPDESK_USER = 'test@example.com'
HELPDESK_API_KEY = 'abc123'


@ddt.ddt
@override_settings(
    ECOMMERCE_PUBLIC_URL_ROOT=TEST_PUBLIC_URL_ROOT,
    ECOMMERCE_API_URL=TEST_API_URL, ECOMMERCE_API_SIGNING_KEY=TEST_API_SIGNING_KEY,
    HELPDESK=HELPDESK, HELPDESK_URL=HELPDESK_URL, HELPDESK_USER=HELPDESK_USER,
    HELPDESK_API_KEY=HELPDESK_API_KEY
)
class TestRefundSignal(TestCase):
    """
    Exercises logic triggered by the UNENROLL_DONE signal.
    """

    def setUp(self):
        super(TestRefundSignal, self).setUp()
        self.requester = UserFactory(username="test-requester")
        self.student = UserFactory(
            username="test-student",
            email="test-student@example.com",
        )
        self.course_enrollment = CourseEnrollmentFactory(
            user=self.student,
            course_id=CourseKey.from_string('course-v1:org+course+run'),
            mode=CourseMode.VERIFIED,
        )
        self.course_enrollment.refundable = mock.Mock(return_value=True)

    def send_signal(self, skip_refund=False):
        """
        DRY helper: emit the UNENROLL_DONE signal, as is done in
        common.djangoapps.student.models after a successful unenrollment.
        """
        UNENROLL_DONE.send(sender=None, course_enrollment=self.course_enrollment, skip_refund=skip_refund)

    @override_settings(
        ECOMMERCE_PUBLIC_URL_ROOT=None,
        ECOMMERCE_API_URL=None,
        ECOMMERCE_API_SIGNING_KEY=None,
    )
    def test_no_service(self):
        """
        Ensure that the receiver quietly bypasses attempts to initiate
        refunds when there is no external service configured.
        """
        with mock.patch('commerce.signals.refund_seat') as mock_refund_seat:
            self.send_signal()
            self.assertFalse(mock_refund_seat.called)

    @mock.patch('commerce.signals.refund_seat')
    def test_receiver(self, mock_refund_seat):
        """
        Ensure that the UNENROLL_DONE signal triggers correct calls to
        refund_seat(), when it is appropriate to do so.

        TODO (jsa): ideally we would assert that the signal receiver got wired
        up independently of the import statement in this module.  I'm not aware
        of any reliable / sane way to do this.
        """
        self.send_signal()
        self.assertTrue(mock_refund_seat.called)
        self.assertEqual(mock_refund_seat.call_args[0], (self.course_enrollment, self.student))

        # if skip_refund is set to True in the signal, we should not try to initiate a refund.
        mock_refund_seat.reset_mock()
        self.send_signal(skip_refund=True)
        self.assertFalse(mock_refund_seat.called)

        # if the course_enrollment is not refundable, we should not try to initiate a refund.
        mock_refund_seat.reset_mock()
        self.course_enrollment.refundable = mock.Mock(return_value=False)
        self.send_signal()
        self.assertFalse(mock_refund_seat.called)

    @mock.patch('commerce.signals.refund_seat')
    @mock.patch('commerce.signals.get_request_user', return_value=None)
    def test_requester(self, mock_get_request_user, mock_refund_seat):
        """
        Ensure the right requester is specified when initiating refunds.
        """
        # no HTTP request/user: auth to commerce service as the unenrolled student.
        self.send_signal()
        self.assertTrue(mock_refund_seat.called)
        self.assertEqual(mock_refund_seat.call_args[0], (self.course_enrollment, self.student))

        # HTTP user is the student: auth to commerce service as the unenrolled student.
        mock_get_request_user.return_value = self.student
        mock_refund_seat.reset_mock()
        self.send_signal()
        self.assertTrue(mock_refund_seat.called)
        self.assertEqual(mock_refund_seat.call_args[0], (self.course_enrollment, self.student))

        # HTTP user is another user: auth to commerce service as the requester.
        mock_get_request_user.return_value = self.requester
        mock_refund_seat.reset_mock()
        self.send_signal()
        self.assertTrue(mock_refund_seat.called)
        self.assertEqual(mock_refund_seat.call_args[0], (self.course_enrollment, self.requester))

        # HTTP user is another server (AnonymousUser): do not try to initiate a refund at all.
        mock_get_request_user.return_value = AnonymousUser()
        mock_refund_seat.reset_mock()
        self.send_signal()
        self.assertFalse(mock_refund_seat.called)

    @mock.patch('commerce.signals.log.warning')
    def test_not_authorized_warning(self, mock_log_warning):
        """
        Ensure that expected authorization issues are logged as warnings.
        """
        with mock_create_refund(status=403):
            refund_seat(self.course_enrollment, UserFactory())
            self.assertTrue(mock_log_warning.called)

    @mock.patch('commerce.signals.log.exception')
    def test_error_logging(self, mock_log_exception):
        """
        Ensure that unexpected Exceptions are logged as errors (but do not
        break program flow).
        """
        with mock_create_refund(status=500):
            self.send_signal()
            self.assertTrue(mock_log_exception.called)

    @mock.patch('commerce.signals.send_refund_notification')
    def test_notification(self, mock_send_notification):
        """
        Ensure the notification function is triggered when refunds are
        initiated
        """
        with mock_create_refund(status=200, response=[1, 2, 3]):
            self.send_signal()
            self.assertTrue(mock_send_notification.called)

    @mock.patch('commerce.signals.send_refund_notification')
    def test_notification_no_refund(self, mock_send_notification):
        """
        Ensure the notification function is NOT triggered when no refunds are
        initiated
        """
        with mock_create_refund(status=200, response=[]):
            self.send_signal()
            self.assertFalse(mock_send_notification.called)

    @mock.patch('commerce.signals.send_refund_notification')
    @ddt.data(
        CourseMode.HONOR,
        CourseMode.PROFESSIONAL,
        CourseMode.AUDIT,
        CourseMode.NO_ID_PROFESSIONAL_MODE,
        CourseMode.CREDIT_MODE,
    )
    def test_notification_not_verified(self, mode, mock_send_notification):
        """
        Ensure the notification function is NOT triggered when the
        unenrollment is for any mode other than verified (i.e. any mode other
        than one for which refunds are presently supported).  See the
        TODO associated with XCOM-371 in the signals module in the commerce
        package for more information.
        """
        self.course_enrollment.mode = mode
        with mock_create_refund(status=200, response=[1, 2, 3]):
            self.send_signal()
            self.assertFalse(mock_send_notification.called)

    @mock.patch('commerce.signals.send_refund_notification', side_effect=Exception("Splat!"))
    @mock.patch('commerce.signals.log.warning')
    def test_notification_error(self, mock_log_warning, mock_send_notification):
        """
        Ensure an error occuring during notification does not break program
        flow, but a warning is logged.
        """
        with mock_create_refund(status=200, response=[1, 2, 3]):
            self.send_signal()
            self.assertTrue(mock_send_notification.called)
            self.assertTrue(mock_log_warning.called)

    @mock.patch('openedx.core.djangoapps.theming.helpers.is_request_in_themed_site', return_value=True)
    def test_notification_themed_site(self, mock_is_request_in_themed_site):  # pylint: disable=unused-argument
        """
        Ensure the notification function raises an Exception if used in the
        context of themed site.
        """
        with self.assertRaises(NotImplementedError):
            send_refund_notification(self.course_enrollment, [1, 2, 3])

    @ddt.data('email@example.com', 'üñîcode.email@example.com')
    @mock.patch('common.djangoapps.util.views.create_helpdesk_ticket')
    def test_send_refund_notification(self, student_email, mock_helpdesk):
        """ Verify the support team is notified of the refund request. """
        refund_ids = [1, 2, 3]

        # pass a student with unicode and ascii email to ensure that
        # generate_refund_notification_body can handle formatting a unicode
        # message
        self.student.email = student_email
        send_refund_notification(self.course_enrollment, refund_ids)
        body = generate_refund_notification_body(self.student, refund_ids)
        mock_helpdesk.assert_called_with(
            self.student.profile.name,
            self.student.email,
            "[Refund] User-Requested Refund",
            body,
            ['auto_refund']
        )
