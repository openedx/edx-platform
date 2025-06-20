# pylint: disable = W0212
"""
Test for account level migration command
"""
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core.management import call_command

from openedx.core.djangoapps.notifications.email_notifications import EmailCadence
from openedx.core.djangoapps.notifications.models import (
    CourseNotificationPreference,
    NotificationPreference
)
from openedx.core.djangoapps.notifications.management.commands.migrate_preferences_to_account_level_model import Command

User = get_user_model()
COMMAND_MODULE = 'openedx.core.djangoapps.notifications.management.commands.migrate_preferences_to_account_level_model'


class MigrateNotificationPreferencesTestCase(TestCase):
    """Test cases for the migrate_preferences_to_account_level_model management command."""

    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com')
        self.user3 = User.objects.create_user(username='user3', email='user3@example.com')

        # Sample notification preference config
        self.sample_config = {
            "grading": {
                "enabled": True,
                "notification_types": {
                    "core": {
                        "web": True,
                        "push": True,
                        "email": True,
                        "email_cadence": "Daily"
                    },
                    "ora_grade_assigned": {
                        "web": True,
                        "push": False,
                        "email": True,
                        "email_cadence": "Daily"
                    }
                },
                "core_notification_types": ["grade_assigned", "grade_updated"]
            },
            "discussion": {
                "enabled": True,
                "notification_types": {
                    "core": {
                        "web": False,
                        "push": True,
                        "email": False,
                        "email_cadence": "Weekly"
                    },
                    "new_post": {
                        "web": True,
                        "push": True,
                        "email": True,
                        "email_cadence": "Immediately"
                    }
                },
                "core_notification_types": ["new_response", "new_comment"]
            }
        }

    def tearDown(self):
        """Clean up test data."""
        CourseNotificationPreference.objects.all().delete()
        NotificationPreference.objects.all().delete()
        User.objects.all().delete()

    def test_get_user_ids_to_process(self):
        """Test that _get_user_ids_to_process returns correct user IDs."""
        # Create course preferences for users
        CourseNotificationPreference.objects.create(
            user=self.user1,
            course_id='course-v1:Test+Course+1',
            notification_preference_config=self.sample_config
        )
        CourseNotificationPreference.objects.create(
            user=self.user2,
            course_id='course-v1:Test+Course+2',
            notification_preference_config=self.sample_config
        )

        command = Command()
        user_ids = list(command._get_user_ids_to_process())

        self.assertEqual(len(user_ids), 2)
        self.assertIn(self.user1.id, user_ids)
        self.assertIn(self.user2.id, user_ids)

    def test_create_preference_object(self):
        """Test that _create_preference_object creates correct NotificationPreference instance."""
        command = Command()
        values = {
            'web': True,
            'push': False,
            'email': True,
            'email_cadence': 'Weekly'
        }

        preference = command._create_preference_object(
            user_id=self.user1.id,
            app_name='grading',
            notification_type='ora_grade_assigned',
            values=values
        )

        self.assertEqual(preference.user_id, self.user1.id)
        self.assertEqual(preference.app, 'grading')
        self.assertEqual(preference.type, 'ora_grade_assigned')
        self.assertTrue(preference.web)
        self.assertFalse(preference.push)
        self.assertTrue(preference.email)
        self.assertEqual(preference.email_cadence, 'Weekly')

    def test_create_preference_object_with_defaults(self):
        """Test _create_preference_object with missing values uses defaults."""
        command = Command()
        values = {'web': True}  # Missing other values

        preference = command._create_preference_object(
            user_id=self.user1.id,
            app_name='grading',
            notification_type='test_type',
            values=values
        )

        self.assertTrue(preference.web)
        self.assertIsNone(preference.push)
        self.assertIsNone(preference.email)
        self.assertEqual(preference.email_cadence, EmailCadence.DAILY)

    @patch(f'{COMMAND_MODULE}.aggregate_notification_configs')
    def test_process_user_preferences_success(self, mock_aggregate):
        """Test successful processing of user preferences."""
        # Setup
        CourseNotificationPreference.objects.create(
            user=self.user1,
            course_id='course-v1:Test+Course+1',
            notification_preference_config=self.sample_config
        )

        mock_aggregate.return_value = {
            'grading': {
                'notification_types': {
                    'core': {'web': True, 'push': True, 'email': True, 'email_cadence': 'Daily'},
                    'grade_assigned': {'web': True, 'push': False, 'email': True, 'email_cadence': 'Daily'}
                },
                'core_notification_types': ['grade_updated']
            }
        }

        command = Command()
        preferences = command._process_batch([self.user1.id])

        self.assertEqual(len(preferences), 2)  # grade_assigned + grade_updated

        # Check grade_assigned preference
        grade_assigned_pref = next(p for p in preferences if p.type == 'grade_assigned')
        self.assertEqual(grade_assigned_pref.app, 'grading')
        self.assertTrue(grade_assigned_pref.web)
        self.assertFalse(grade_assigned_pref.push)
        self.assertTrue(grade_assigned_pref.email)

        # Check core notification type
        grade_updated_pref = next(p for p in preferences if p.type == 'grade_updated')
        self.assertEqual(grade_updated_pref.app, 'grading')
        self.assertTrue(grade_updated_pref.web)
        self.assertTrue(grade_updated_pref.push)
        self.assertTrue(grade_updated_pref.email)

    @patch(f'{COMMAND_MODULE}.aggregate_notification_configs')
    def test_process_user_preferences_no_course_preferences(self, mock_aggregate):
        """Test processing user with no course preferences."""
        command = Command()
        preferences = command._process_batch([self.user1.id])

        self.assertEqual(len(preferences), 0)
        mock_aggregate.assert_not_called()

    @patch(f'{COMMAND_MODULE}.aggregate_notification_configs')
    def test_process_user_preferences_malformed_data(self, mock_aggregate):
        """Test handling of malformed notification config data."""
        CourseNotificationPreference.objects.create(
            user=self.user1,
            course_id='course-v1:Test+Course+1',
            notification_preference_config=self.sample_config
        )

        # Mock malformed data
        mock_aggregate.return_value = {
            'grading': 'invalid_string',  # Should be dict
            'discussion': {
                'notification_types': 'invalid_string',  # Should be dict
                'core_notification_types': []
            },
            'updates': {
                'notification_types': {
                    'core': {'web': True, 'push': True, 'email': True},
                    'invalid_type': None  # Invalid notification type data
                },
                'core_notification_types': 'invalid_string'  # Should be list
            }
        }

        command = Command()
        with self.assertLogs(level='WARNING') as log:
            preferences = command._process_batch([self.user1.id])

        self.assertEqual(len(preferences), 0)
        self.assertIn('Malformed app_config', log.output[0])

    @patch(f'{COMMAND_MODULE}.logger')
    def test_handle_dry_run_mode(self, mock_logger):
        """Test command execution in dry-run mode."""
        CourseNotificationPreference.objects.create(
            user=self.user1,
            course_id='course-v1:Test+Course+1',
            notification_preference_config=self.sample_config
        )

        with patch.object(Command, '_process_batch') as mock_process:
            mock_process.return_value = [
                NotificationPreference(
                    user_id=self.user1.id,
                    app='grading',
                    type='test_type',
                    web=True,
                    push=False,
                    email=True,
                    email_cadence='Daily'
                )
            ]

            call_command('migrate_preferences_to_account_level_model', '--dry-run', '--batch-size=1')

        # Check that no actual database changes were made
        self.assertEqual(NotificationPreference.objects.count(), 0)

        # Verify dry-run logging
        mock_logger.info.assert_any_call(
            'Performing a DRY RUN. No changes will be made to the database.'
        )

    def test_handle_normal_execution(self):
        """Test normal command execution without dry-run."""
        CourseNotificationPreference.objects.create(
            user=self.user1,
            course_id='course-v1:Test+Course+1',
            notification_preference_config=self.sample_config
        )

        # Create existing account preferences to test deletion
        NotificationPreference.objects.create(
            user=self.user1,
            app='old_app',
            type='old_type',
            web=True,
            push=False,
            email=False,
            email_cadence='Daily'
        )

        with patch.object(Command, '_process_batch') as mock_process:
            mock_process.return_value = [
                NotificationPreference(
                    user_id=self.user1.id,
                    app='grading',
                    type='test_type',
                    web=True,
                    push=False,
                    email=True,
                    email_cadence='Daily'
                )
            ]

            call_command('migrate_preferences_to_account_level_model', '--batch-size=1')

        # Verify old preferences were deleted and new ones created
        self.assertEqual(NotificationPreference.objects.count(), 1)
        new_pref = NotificationPreference.objects.first()
        self.assertEqual(new_pref.app, 'grading')
        self.assertEqual(new_pref.type, 'test_type')

    @patch(f'{COMMAND_MODULE}.transaction.atomic')
    def test_migrate_preferences_to_account_level_model(self, mock_atomic):
        """Test that users are processed in batches correctly."""
        # Mock atomic to avoid transaction issues during testing
        mock_atomic.return_value.__enter__ = Mock()
        mock_atomic.return_value.__exit__ = Mock(return_value=None)

        # Create course preferences for multiple users
        for i, user in enumerate([self.user1, self.user2, self.user3]):
            CourseNotificationPreference.objects.create(
                user=user,
                course_id=f'course-v1:Test+Course+{i}',
                notification_preference_config=self.sample_config
            )

        call_command('migrate_preferences_to_account_level_model', '--batch-size=2')
        # Check that preferences were created for each user
        self.assertEqual(NotificationPreference.objects.count(), 18)

    def test_command_arguments(self):
        """Test that command arguments are handled correctly."""
        command = Command()
        parser = command.create_parser('test', 'migrate_preferences_to_account_level_model')

        # Test default arguments
        options = parser.parse_args([])
        self.assertEqual(options.batch_size, 1000)
        self.assertFalse(options.dry_run)

        # Test custom arguments
        options = parser.parse_args(['--batch-size', '500', '--dry-run'])
        self.assertEqual(options.batch_size, 500)
        self.assertTrue(options.dry_run)

    @patch(f'{COMMAND_MODULE}.aggregate_notification_configs')
    def test_process_user_preferences_with_core_types(self, mock_aggregate):
        """Test processing of core notification types specifically."""
        CourseNotificationPreference.objects.create(
            user=self.user1,
            course_id='course-v1:Test+Course+1',
            notification_preference_config=self.sample_config
        )

        mock_aggregate.return_value = {
            'discussion': {
                'notification_types': {
                    'core': {'web': False, 'push': True, 'email': False, 'email_cadence': 'Weekly'}
                },
                'core_notification_types': ['new_response', 'new_comment', None, 123]  # Include invalid types
            }
        }

        command = Command()
        with self.assertLogs(level='WARNING') as log:
            preferences = command._process_batch([self.user1.id])

        # Should create 2 valid core preferences (ignoring None and 123)
        valid_prefs = [p for p in preferences if p.type in ['new_response', 'new_comment']]
        self.assertEqual(len(valid_prefs), 2)

        # Check that invalid core types were logged as warnings
        warning_logs = [log for log in log.output if 'Skipping malformed core_type_name' in log]
        self.assertEqual(len(warning_logs), 2)

    def test_progress_logging(self):
        """Test that progress is logged at appropriate intervals."""
        # Create enough users to trigger progress logging
        users = []
        for i in range(10):
            user = User.objects.create_user(username=f'userX{i}', email=f'userx{i}@example.com')
            users.append(user)
            CourseNotificationPreference.objects.create(
                user=user,
                course_id=f'course-v1:Test+Course+{i}',
                notification_preference_config=self.sample_config
            )

        with patch.object(Command, '_process_batch') as mock_process:
            mock_process.return_value = []

            with patch(f'{COMMAND_MODULE}.logger') as mock_logger:
                call_command('migrate_preferences_to_account_level_model', '--batch-size=1')

                # Check that progress was logged (every 5 batches)
                progress_calls = [call for call in mock_logger.info.call_args_list
                                  if 'PROGRESS:' in str(call)]
                self.assertGreater(len(progress_calls), 0)

    def test_empty_batch_handling(self):
        """Test handling when no preferences need to be created."""
        CourseNotificationPreference.objects.create(
            user=self.user1,
            course_id='course-v1:Test+Course+1',
            notification_preference_config=self.sample_config
        )

        with patch.object(Command, '_process_batch') as mock_process:
            mock_process.return_value = []  # No preferences to create

            with patch(f'{COMMAND_MODULE}.logger') as mock_logger:
                call_command('migrate_preferences_to_account_level_model', '--batch-size=1')

                # Should log that no preferences were created
                no_prefs_calls = [call for call in mock_logger.info.call_args_list
                                  if 'No preferences to create' in str(call)]
                self.assertEqual(len(no_prefs_calls), 1)
