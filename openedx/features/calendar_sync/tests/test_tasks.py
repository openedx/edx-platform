"""
Tests for the Sending activation email celery tasks
"""


import mock
from django.conf import settings
from django.test import TestCase
from six.moves import range

from edx_ace.errors import ChannelError, RecoverableChannelDeliveryError
from lms.djangoapps.courseware.tests.factories import UserFactory
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.features.calendar_sync.tasks import send_calendar_sync_email
from openedx.features.calendar_sync.views.management import compose_calendar_sync_email


class SendCalendarSyncEmailTestCase(TestCase):
    """
    Test for send activation email to user
    """
    def setUp(self):
        """ Setup components used by each test."""
        super(SendCalendarSyncEmailTestCase, self).setUp()
        self.user = UserFactory()
        self.course_overview = CourseOverviewFactory()
        self.msg = compose_calendar_sync_email(self.user, self.course_overview)

    @mock.patch('time.sleep', mock.Mock(return_value=None))
    @mock.patch('openedx.features.calendar_sync.tasks.log')
    @mock.patch(
        'openedx.features.calendar_sync.tasks.ace.send',
        mock.Mock(side_effect=RecoverableChannelDeliveryError(None, None))
    )
    def test_RetrySendUntilFail(self, mock_log):
        """
        Tests retries when the activation email doesn't send
        """
        from_address = 'task_testing@example.com'
        email_max_attempts = settings.RETRY_ACTIVATION_EMAIL_MAX_ATTEMPTS

        send_calendar_sync_email.delay(str(self.msg), from_address=from_address)

        # Asserts sending email retry logging.
        for attempt in range(email_max_attempts):
            mock_log.info.assert_any_call(
                'Retrying sending email to user {dest_addr}, attempt # {attempt} of {max_attempts}'.format(
                    dest_addr=self.user.email,
                    attempt=attempt,
                    max_attempts=email_max_attempts
                ))
        self.assertEqual(mock_log.info.call_count, 6)

        # Asserts that the error was logged on crossing max retry attempts.
        mock_log.error.assert_called_with(
            'Unable to send calendar sync email to user from "%s" to "%s"',
            from_address,
            self.user.email,
            exc_info=True
        )
        self.assertEqual(mock_log.error.call_count, 1)

    @mock.patch('openedx.features.calendar_sync.tasks.log')
    @mock.patch('openedx.features.calendar_sync.tasks.ace.send', mock.Mock(side_effect=ChannelError))
    def test_UnrecoverableSendError(self, mock_log):
        """
        Tests that a major failure of the send is logged
        """
        from_address = 'task_testing@example.com'

        send_calendar_sync_email.delay(str(self.msg), from_address=from_address)

        # Asserts that the error was logged
        mock_log.exception.assert_called_with(
            'Unable to send calendar sync email to user from "%s" to "%s"',
            from_address,
            self.user.email
        )

        # Assert that nothing else was logged
        self.assertEqual(mock_log.info.call_count, 0)
        self.assertEqual(mock_log.error.call_count, 0)
        self.assertEqual(mock_log.exception.call_count, 1)
