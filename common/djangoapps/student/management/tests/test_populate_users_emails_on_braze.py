"""
Unittests for populate_marketing_opt_in_user_attribute management command.
"""
from unittest.mock import patch, MagicMock

from braze.exceptions import BrazeClientError
from django.core.management import call_command
from django.test import TestCase
from testfixtures import LogCapture

from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangolib.testing.utils import skip_unless_lms

LOGGER_NAME = 'common.djangoapps.student.management.commands.populate_users_emails_on_braze'


@skip_unless_lms
class TestPopulateUsersEmailsOnBraze(TestCase):
    """
    Tests for PopulateUsersEmailsOnBraze management command.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        for index in range(15):
            user = UserFactory()

    @patch('common.djangoapps.student.management.commands.populate_users_emails_on_braze.BrazeClient.track_user')
    def test_command_updates_users_on_braze(self, track_user):
        """
        Test that Braze API is called successfully for all users
        """
        track_user.return_value = MagicMock()
        call_command('populate_users_emails_on_braze', batch_delay=0)
        assert track_user.called

    @patch('common.djangoapps.student.management.commands.populate_users_emails_on_braze.BrazeClient.track_user')
    def test_logs_for_success(self, track_user):
        """
        Test logs for a successful run of updating user accounts on Braze
        """
        track_user.return_value = MagicMock()
        with LogCapture(LOGGER_NAME) as log:
            call_command(
                'populate_users_emails_on_braze',
                batch_size=5,
                batch_delay=0,
            )
            log.check(
                (LOGGER_NAME, 'INFO', 'Processing users with user ids in 0 - 4 range'),
                (LOGGER_NAME, 'INFO', 'Processing users with user ids in 5 - 9 range'),
                (LOGGER_NAME, 'INFO', 'Processing users with user ids in 10 - 14 range'),
                (LOGGER_NAME, 'INFO', 'Processing users with user ids in 15 - 19 range'),
            )

    @patch('common.djangoapps.student.management.commands.populate_users_emails_on_braze.BrazeClient.track_user')
    def test_logs_for_failure(self, track_user):
        """
        Test logs for when the update to Braze fails
        """
        track_user.side_effect = BrazeClientError('Update to attributes failed.')
        with LogCapture(LOGGER_NAME) as log:
            call_command(
                'populate_users_emails_on_braze',
                batch_size=5,
                batch_delay=0,
            )
            log.check_present(
                (LOGGER_NAME, 'ERROR', 'Failed to update attributes. Error: Update to attributes failed.'),
            )

    @patch('common.djangoapps.student.management.commands.populate_users_emails_on_braze.BrazeClient.track_user')
    def test_running_a_specific_batch(self, track_user):
        """
        Test running command for a specific batch of users
        """
        track_user.return_value = MagicMock()
        with LogCapture(LOGGER_NAME) as log:
            call_command(
                'populate_users_emails_on_braze',
                batch_size=5,
                batch_delay=0,
                starting_user_id=2,
                ending_user_id=13,
            )
            log.check(
                (LOGGER_NAME, 'INFO', 'Processing users with user ids in 2 - 6 range'),
                (LOGGER_NAME, 'INFO', 'Processing users with user ids in 7 - 11 range'),
                (LOGGER_NAME, 'INFO', 'Processing users with user ids in 12 - 16 range'),
            )
