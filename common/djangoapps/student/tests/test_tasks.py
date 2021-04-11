"""
Tests for the Sending activation email celery tasks
"""


import mock
from django.conf import settings
from django.test import TestCase
from six.moves import range

from edx_ace.errors import ChannelError, RecoverableChannelDeliveryError
from lms.djangoapps.courseware.tests.factories import UserFactory
from common.djangoapps.student.models import Registration
from common.djangoapps.student.tasks import send_activation_email
from common.djangoapps.student.views.management import compose_activation_email


class SendActivationEmailTestCase(TestCase):
    """
    Test for send activation email to user
    """
    def setUp(self):
        """ Setup components used by each test."""
        super(SendActivationEmailTestCase, self).setUp()
        self.student = UserFactory()

        registration = Registration()
        registration.register(self.student)

        self.msg = compose_activation_email("http://www.example.com", self.student, registration)

    def test_ComposeEmail(self):
        """
        Tests that attributes of the message are being filled correctly in compose_activation_email
        """
        self.assertEqual(self.msg.recipient.username, self.student.username)
        self.assertEqual(self.msg.recipient.email_address, self.student.email)
        self.assertEqual(self.msg.context['routed_user'], self.student.username)
        self.assertEqual(self.msg.context['routed_user_email'], self.student.email)
        self.assertEqual(self.msg.context['routed_profile_name'], '')

    @mock.patch('time.sleep', mock.Mock(return_value=None))
    @mock.patch('common.djangoapps.student.tasks.log')
    @mock.patch('common.djangoapps.student.tasks.ace.send', mock.Mock(side_effect=RecoverableChannelDeliveryError(None, None)))
    def test_RetrySendUntilFail(self, mock_log):
        """
        Tests retries when the activation email doesn't send
        """
        from_address = 'task_testing@example.com'
        email_max_attempts = settings.RETRY_ACTIVATION_EMAIL_MAX_ATTEMPTS

        send_activation_email.delay(str(self.msg), from_address=from_address)

        # Asserts sending email retry logging.
        for attempt in range(email_max_attempts):
            mock_log.info.assert_any_call(
                'Retrying sending email to user {dest_addr}, attempt # {attempt} of {max_attempts}'.format(
                    dest_addr=self.student.email,
                    attempt=attempt,
                    max_attempts=email_max_attempts
                ))
        self.assertEqual(mock_log.info.call_count, 6)

        # Asserts that the error was logged on crossing max retry attempts.
        mock_log.error.assert_called_with(
            'Unable to send activation email to user from "%s" to "%s"',
            from_address,
            self.student.email,
            exc_info=True
        )
        self.assertEqual(mock_log.error.call_count, 1)

    @mock.patch('common.djangoapps.student.tasks.log')
    @mock.patch('common.djangoapps.student.tasks.ace.send', mock.Mock(side_effect=ChannelError))
    def test_UnrecoverableSendError(self, mock_log):
        """
        Tests that a major failure of the send is logged
        """
        from_address = 'task_testing@example.com'

        send_activation_email.delay(str(self.msg), from_address=from_address)

        # Asserts that the error was logged
        mock_log.exception.assert_called_with(
            'Unable to send activation email to user from "%s" to "%s"',
            from_address,
            self.student.email,
        )

        # Assert that nothing else was logged
        self.assertEqual(mock_log.info.call_count, 0)
        self.assertEqual(mock_log.error.call_count, 0)
        self.assertEqual(mock_log.exception.call_count, 1)
