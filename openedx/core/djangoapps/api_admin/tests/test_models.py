# pylint: disable=missing-docstring


from smtplib import SMTPException

import ddt
import mock
import six
from django.db import IntegrityError
from django.test import TestCase

from openedx.core.djangoapps.api_admin.models import ApiAccessConfig, ApiAccessRequest
from openedx.core.djangoapps.api_admin.models import log as model_log
from openedx.core.djangoapps.api_admin.tests.factories import ApiAccessRequestFactory
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.core.djangolib.testing.utils import skip_unless_lms
from common.djangoapps.student.tests.factories import UserFactory


@ddt.ddt
@skip_unless_lms
class ApiAccessRequestTests(TestCase):

    def setUp(self):
        super(ApiAccessRequestTests, self).setUp()
        self.user = UserFactory()
        self.request = ApiAccessRequestFactory(user=self.user)

    def test_default_status(self):
        self.assertEqual(self.request.status, ApiAccessRequest.PENDING)
        self.assertFalse(ApiAccessRequest.has_api_access(self.user))

    def test_approve(self):
        self.request.approve()
        self.assertEqual(self.request.status, ApiAccessRequest.APPROVED)

    def test_deny(self):
        self.request.deny()
        self.assertEqual(self.request.status, ApiAccessRequest.DENIED)

    def test_nonexistent_request(self):
        """Test that users who have not requested API access do not get it."""
        other_user = UserFactory()
        self.assertFalse(ApiAccessRequest.has_api_access(other_user))

    @ddt.data(
        (ApiAccessRequest.PENDING, False),
        (ApiAccessRequest.DENIED, False),
        (ApiAccessRequest.APPROVED, True),
    )
    @ddt.unpack
    def test_has_access(self, status, should_have_access):
        self.request.status = status
        self.request.save()
        self.assertEqual(ApiAccessRequest.has_api_access(self.user), should_have_access)

    def test_unique_per_user(self):
        with self.assertRaises(IntegrityError):
            ApiAccessRequestFactory(user=self.user)

    def test_no_access(self):
        self.request.delete()
        self.assertIsNone(ApiAccessRequest.api_access_status(self.user))

    def test_unicode(self):
        request_unicode = six.text_type(self.request)
        self.assertIn(self.request.website, request_unicode)
        self.assertIn(self.request.status, request_unicode)

    def test_retire_user_success(self):
        retire_result = self.request.retire_user(self.user)
        self.assertTrue(retire_result)
        self.assertEqual(self.request.company_address, '')
        self.assertEqual(self.request.company_name, '')
        self.assertEqual(self.request.website, '')
        self.assertEqual(self.request.reason, '')

    def test_retire_user_do_not_exist(self):
        user2 = UserFactory()
        retire_result = self.request.retire_user(user2)
        self.assertFalse(retire_result)


class ApiAccessConfigTests(TestCase):

    def test_unicode(self):
        self.assertEqual(
            six.text_type(ApiAccessConfig(enabled=True)),
            u'ApiAccessConfig [enabled=True]'
        )
        self.assertEqual(
            six.text_type(ApiAccessConfig(enabled=False)),
            u'ApiAccessConfig [enabled=False]'
        )


@skip_unless_lms
class ApiAccessRequestSignalTests(TestCase):
    def setUp(self):
        super(ApiAccessRequestSignalTests, self).setUp()
        self.user = UserFactory()
        self.api_access_request = ApiAccessRequest(user=self.user, site=SiteFactory())
        self.send_new_pending_email_function = 'openedx.core.djangoapps.api_admin.models._send_new_pending_email'
        self.send_decision_email_function = 'openedx.core.djangoapps.api_admin.models._send_decision_email'

    def test_save_signal_success_new_email(self):
        """ Verify that initial save sends new email and no decision email. """
        with mock.patch(self.send_new_pending_email_function) as mock_new_email:
            with mock.patch(self.send_decision_email_function) as mock_decision_email:
                self.api_access_request.save()

        mock_new_email.assert_called_once_with(self.api_access_request)
        self.assertFalse(mock_decision_email.called)

    def test_save_signal_success_decision_email(self):
        """ Verify that updating request status sends decision email and no new email. """
        self.api_access_request.save()

        with mock.patch(self.send_new_pending_email_function) as mock_new_email:
            with mock.patch(self.send_decision_email_function) as mock_decision_email:
                self.api_access_request.approve()

        mock_decision_email.assert_called_once_with(self.api_access_request)
        self.assertFalse(mock_new_email.called)

    def test_save_signal_success_no_emails(self):
        """ Verify that updating request status again sends no emails. """
        self.api_access_request.save()
        self.api_access_request.approve()

        with mock.patch(self.send_new_pending_email_function) as mock_new_email:
            with mock.patch(self.send_decision_email_function) as mock_decision_email:
                self.api_access_request.deny()

        self.assertFalse(mock_decision_email.called)
        self.assertFalse(mock_new_email.called)

    def test_save_signal_failure_email(self):
        """ Verify that saving still functions even on email errors. """
        self.assertIsNone(self.api_access_request.id)

        mail_function = 'openedx.core.djangoapps.api_admin.models.send_mail'
        with mock.patch(mail_function, side_effect=SMTPException):
            with mock.patch.object(model_log, 'exception') as mock_model_log_exception:
                self.api_access_request.save()

        # Verify that initial save logs email errors properly
        mock_model_log_exception.assert_called_once_with(
            u'Error sending API user notification email for request [%s].', self.api_access_request.id
        )
        # Verify object saved
        self.assertIsNotNone(self.api_access_request.id)

        with mock.patch(mail_function, side_effect=SMTPException):
            with mock.patch.object(model_log, 'exception') as mock_model_log_exception:
                self.api_access_request.approve()
        # Verify that updating request status logs email errors properly
        mock_model_log_exception.assert_called_once_with(
            u'Error sending API user notification email for request [%s].', self.api_access_request.id
        )
        # Verify object saved
        self.assertEqual(self.api_access_request.status, ApiAccessRequest.APPROVED)
