# pylint: disable=protected-access
"""
 Test module for the migrate_preferences_to_account_level_model management command.
"""
from io import StringIO
from unittest.mock import Mock, call, patch

from django.core.management import call_command
from django.test import TestCase

from openedx.core.djangoapps.notifications.management.commands.migrate_preferences_to_account_level_model import Command
from openedx.core.djangoapps.notifications.models import CourseNotificationPreference

MODULE_PATH = 'openedx.core.djangoapps.notifications.management.commands.migrate_preferences_to_account_level_model'


class MigratePreferencesToAccountLevelTest(TestCase):
    """Test suite for the migrate_preferences_to_account_level_model management command."""

    def setUp(self):
        """Set up test fixtures."""
        self.command = Command()
        self.command.BATCH_SIZE = 100  # Smaller batch size for testing
        self.command.CHUNK_SIZE = 50

        # Mock logger to capture log messages
        self.logger_patcher = patch(f'{MODULE_PATH}.logger')
        self.mock_logger = self.logger_patcher.start()

    def tearDown(self):
        """Clean up patches."""
        self.logger_patcher.stop()

    def _create_mock_course_preference(self, user_id, config):
        """Helper to create mock CourseNotificationPreference."""
        mock_pref = Mock(spec=CourseNotificationPreference)
        mock_pref.user_id = user_id
        mock_pref.notification_preference_config = config
        return mock_pref

    def _create_sample_config(self):
        """Create sample notification preference configuration."""
        return {
            'discussion': {
                'notification_types': {
                    'new_comment': {
                        'web': True,
                        'email': True,
                        'push': False,
                        'email_cadence': 'Daily'
                    },
                    'core': {
                        'web': True,
                        'email': False,
                        'push': True,
                        'email_cadence': 'Weekly'
                    }
                },
                'core_notification_types': ['new_post', 'post_edited']
            },
            'updates': {
                'notification_types': {
                    'course_update': {
                        'web': False,
                        'email': True,
                        'push': True,
                        'email_cadence': 'Immediate'
                    }
                }
            }
        }

    @patch(f'{MODULE_PATH}.CourseNotificationPreference')
    @patch(f'{MODULE_PATH}.NotificationPreference')
    def test_handle_successful_migration(self, mock_notif_pref_model, mock_course_pref_model):
        """Test successful migration flow."""
        # Setup mock data
        sample_config = self._create_sample_config()
        mock_course_pref = self._create_mock_course_preference(1, sample_config)

        # Mock CourseNotificationPreference queryset
        mock_course_pref_model.objects.count.return_value = 1
        mock_course_pref_model.objects.only.return_value.iterator.return_value = [mock_course_pref]

        # Mock NotificationPreference queryset
        mock_notif_pref_model.objects.values_list.return_value.iterator.return_value = []
        mock_notif_pref_model.objects.bulk_create.return_value = [Mock() for _ in range(4)]

        # Execute command
        self.command.handle()

        # Verify CourseNotificationPreference was queried correctly
        mock_course_pref_model.objects.only.assert_called_once_with('user_id', 'notification_preference_config')
        mock_course_pref_model.objects.count.assert_called_once()

        # Verify NotificationPreference bulk_create was called
        self.assertTrue(mock_notif_pref_model.objects.bulk_create.called)

        # Verify logging
        self.mock_logger.info.assert_any_call("Starting migration of %d course-level preferences", 1)
        self.mock_logger.info.assert_any_call(
            "Migration complete: processed %d course preferences, created %d account preferences", 1, 4)

    @patch(f'{MODULE_PATH}.CourseNotificationPreference')
    @patch(f'{MODULE_PATH}.NotificationPreference')
    def test_dry_run_mode(self, mock_notif_pref_model, mock_course_pref_model):
        """Test dry run mode doesn't create any records."""
        sample_config = self._create_sample_config()
        mock_course_pref = self._create_mock_course_preference(1, sample_config)

        mock_course_pref_model.objects.count.return_value = 1
        mock_course_pref_model.objects.only.return_value.iterator.return_value = [mock_course_pref]
        mock_notif_pref_model.objects.values_list.return_value.iterator.return_value = []

        # Execute with dry_run=True
        self.command.handle(dry_run=True)

        # Verify no bulk_create was called
        mock_notif_pref_model.objects.bulk_create.assert_not_called()

        # Verify dry run logging
        self.mock_logger.info.assert_any_call("DRY RUN MODE - No changes will be made")

    def test_get_existing_preferences(self):
        """Test _get_existing_preferences method."""
        with patch(f'{MODULE_PATH}.NotificationPreference') as mock_model:
            # Mock the values_list iterator
            mock_iterator = Mock()
            mock_iterator.__iter__ = Mock(return_value=iter([
                (1, 'new_comment', 'discussion'),
                (2, 'course_update', 'updates')
            ]))
            mock_model.objects.values_list.return_value.iterator.return_value = mock_iterator

            result = self.command._get_existing_preferences()

            # Verify correct method calls
            mock_model.objects.values_list.assert_called_once_with('user_id', 'type', 'app')

            # Verify result is a set with expected values
            expected = {(1, 'new_comment', 'discussion'), (2, 'course_update', 'updates')}
            self.assertEqual(result, expected)

    def test_get_preference_chunks(self):
        """Test _get_preference_chunks method."""
        mock_prefs = [Mock() for _ in range(125)]  # 125 items to test chunking

        with patch(f'{MODULE_PATH}.CourseNotificationPreference') as mock_model:
            mock_model.objects.only.return_value.iterator.return_value = iter(mock_prefs)

            chunks = list(self.command._get_preference_chunks())

            # Should have 3 chunks: 50, 50, 25
            self.assertEqual(len(chunks), 3)
            self.assertEqual(len(chunks[0]), 50)
            self.assertEqual(len(chunks[1]), 50)
            self.assertEqual(len(chunks[2]), 25)

    def test_expand_notification_types_core(self):
        """Test _expand_notification_types with core type."""
        app_config = {'core_notification_types': ['type1', 'type2', 'type3']}

        result = self.command._expand_notification_types('core', app_config)

        self.assertEqual(result, ['type1', 'type2', 'type3'])

    def test_expand_notification_types_regular(self):
        """Test _expand_notification_types with regular type."""
        app_config = {'core_notification_types': ['type1', 'type2']}

        result = self.command._expand_notification_types('regular_type', app_config)

        self.assertEqual(result, ['regular_type'])

    def test_expand_notification_types_core_empty(self):
        """Test _expand_notification_types with empty core types."""
        app_config = {}

        result = self.command._expand_notification_types('core', app_config)

        self.assertEqual(result, [])

    def test_generate_account_preferences(self):
        """Test _generate_account_preferences method."""
        sample_config = self._create_sample_config()
        course_prefs = [self._create_mock_course_preference(1, sample_config)]
        existing_prefs = {(1, 'existing_type', 'existing_app')}

        with patch(f'{MODULE_PATH}.NotificationPreference') as mock_notif_pref:
            # Mock the NotificationPreference constructor to return distinguishable objects
            mock_instances = []

            def side_effect(**kwargs):
                instance = Mock()
                for key, value in kwargs.items():
                    setattr(instance, key, value)
                mock_instances.append(instance)
                return instance

            mock_notif_pref.side_effect = side_effect

            result = list(self.command._generate_account_preferences(course_prefs, existing_prefs))

            # Should generate 4 preferences:
            # - discussion/new_comment
            # - discussion/new_post (from core expansion)
            # - discussion/post_edited (from core expansion)
            # - updates/course_update
            self.assertEqual(len(result), 4)

            # Verify some specific attributes
            types_created = {(pref.user_id, pref.type, pref.app) for pref in result}
            expected_types = {
                (1, 'new_comment', 'discussion'),
                (1, 'new_post', 'discussion'),
                (1, 'post_edited', 'discussion'),
                (1, 'course_update', 'updates')
            }
            self.assertEqual(types_created, expected_types)

    def test_generate_account_preferences_with_duplicates(self):
        """Test _generate_account_preferences skips existing preferences."""
        sample_config = self._create_sample_config()
        course_prefs = [self._create_mock_course_preference(1, sample_config)]
        existing_prefs = {(1, 'new_comment', 'discussion'), (1, 'new_post', 'discussion')}

        with patch(f'{MODULE_PATH}.NotificationPreference') as mock_notif_pref:
            mock_instances = []

            def side_effect(**kwargs):
                instance = Mock()
                for key, value in kwargs.items():
                    setattr(instance, key, value)
                mock_instances.append(instance)
                return instance

            mock_notif_pref.side_effect = side_effect

            result = list(self.command._generate_account_preferences(course_prefs, existing_prefs))

            # Should only generate 2 preferences (skipping the 2 existing ones)
            self.assertEqual(len(result), 2)

            types_created = {(pref.user_id, pref.type, pref.app) for pref in result}
            expected_types = {
                (1, 'post_edited', 'discussion'),
                (1, 'course_update', 'updates')
            }
            self.assertEqual(types_created, expected_types)

    def test_generate_account_preferences_empty_config(self):
        """Test _generate_account_preferences with empty config."""
        course_prefs = [self._create_mock_course_preference(1, {})]
        existing_prefs = set()

        result = list(self.command._generate_account_preferences(course_prefs, existing_prefs))

        self.assertEqual(len(result), 0)

    def test_generate_account_preferences_none_config(self):
        """Test _generate_account_preferences with None config."""
        course_prefs = [self._create_mock_course_preference(1, None)]
        existing_prefs = set()

        # This should not raise any exceptions
        result = list(self.command._generate_account_preferences(course_prefs, existing_prefs))

        self.assertEqual(len(result), 0)

    def test_generate_account_preferences_non_dict_config(self):
        """Test _generate_account_preferences with non-dict config."""
        course_prefs = [self._create_mock_course_preference(1, "not_a_dict")]
        existing_prefs = set()

        # This should not raise any exceptions
        result = list(self.command._generate_account_preferences(course_prefs, existing_prefs))

        self.assertEqual(len(result), 0)

    @patch(f'{MODULE_PATH}.transaction')
    @patch(f'{MODULE_PATH}.NotificationPreference')
    def test_bulk_create_preferences_success(self, mock_notif_pref_model, mock_transaction):
        """Test successful bulk_create_preferences."""
        mock_preferences = [Mock() for _ in range(5)]
        mock_notif_pref_model.objects.bulk_create.return_value = mock_preferences

        result = self.command._bulk_create_preferences(mock_preferences, 100)

        self.assertEqual(result, 5)
        mock_notif_pref_model.objects.bulk_create.assert_called_once_with(
            mock_preferences, batch_size=100, ignore_conflicts=True
        )

    @patch(f'{MODULE_PATH}.transaction')
    @patch(f'{MODULE_PATH}.NotificationPreference')
    def test_bulk_create_preferences_with_exception(self, mock_notif_pref_model, mock_transaction):
        """Test bulk_create_preferences with exception and fallback."""
        mock_preferences = [Mock(user_id=i) for i in range(3)]

        # Make bulk_create raise an exception
        mock_notif_pref_model.objects.bulk_create.side_effect = Exception("Database error")

        # Mock individual save operations
        for pref in mock_preferences:
            pref.save.return_value = None

        with patch.object(self.command, '_fallback_individual_create', return_value=2) as mock_fallback:
            result = self.command._bulk_create_preferences(mock_preferences, 100)

            # Should have called fallback
            mock_fallback.assert_called_once_with(mock_preferences)
            self.assertEqual(result, 2)

            # Should have logged the error
            self.mock_logger.error.assert_called_once()

    def test_fallback_individual_create_success(self):
        """Test _fallback_individual_create with successful saves."""
        mock_preferences = [Mock(user_id=i) for i in range(3)]
        for pref in mock_preferences:
            pref.save.return_value = None

        result = self.command._fallback_individual_create(mock_preferences)

        self.assertEqual(result, 3)
        for pref in mock_preferences:
            pref.save.assert_called_once()

    def test_fallback_individual_create_with_failures(self):
        """Test _fallback_individual_create with some failures."""
        mock_preferences = [Mock(user_id=i) for i in range(3)]

        # Make the second preference fail
        mock_preferences[0].save.return_value = None
        mock_preferences[1].save.side_effect = Exception("Save failed")
        mock_preferences[2].save.return_value = None

        result = self.command._fallback_individual_create(mock_preferences)

        self.assertEqual(result, 2)  # 2 successful saves
        self.mock_logger.warning.assert_called_once()

    def test_bulk_create_preferences_empty_list(self):
        """Test _bulk_create_preferences with empty list."""
        result = self.command._bulk_create_preferences([], 100)
        self.assertEqual(result, 0)

    @patch(
        f'{MODULE_PATH}.CourseNotificationPreference')
    @patch(f'{MODULE_PATH}.NotificationPreference')
    def test_handle_with_custom_batch_size(self, mock_notif_pref_model, mock_course_pref_model):
        """Test handle method with custom batch size."""
        sample_config = self._create_sample_config()
        mock_course_pref = self._create_mock_course_preference(1, sample_config)

        mock_course_pref_model.objects.count.return_value = 1
        mock_course_pref_model.objects.only.return_value.iterator.return_value = [mock_course_pref]
        mock_notif_pref_model.objects.values_list.return_value.iterator.return_value = []
        mock_notif_pref_model.objects.bulk_create.return_value = [Mock() for _ in range(4)]

        # Execute with custom batch size
        self.command.handle(batch_size=500)

        # Verify bulk_create was called with custom batch size
        args, kwargs = mock_notif_pref_model.objects.bulk_create.call_args
        self.assertEqual(kwargs['batch_size'], 500)

    def test_add_arguments(self):
        """Test add_arguments method."""
        parser = Mock()
        self.command.add_arguments(parser)

        # Verify parser.add_argument was called for each expected argument
        expected_calls = [
            call('--dry-run', action='store_true', help='Show what would be migrated without making changes'),
            call('--batch-size', type=int, default=self.command.BATCH_SIZE,
                 help=f'Batch size for bulk operations (default: {self.command.BATCH_SIZE})'),
        ]
        parser.add_argument.assert_has_calls(expected_calls, any_order=True)

    @patch(f'{MODULE_PATH}.CourseNotificationPreference')
    @patch(f'{MODULE_PATH}.NotificationPreference')
    def test_integration_with_call_command(self, mock_notif_pref_model, mock_course_pref_model):
        """Test integration using Django's call_command."""
        sample_config = self._create_sample_config()
        mock_course_pref = self._create_mock_course_preference(1, sample_config)

        mock_course_pref_model.objects.count.return_value = 1
        mock_course_pref_model.objects.only.return_value.iterator.return_value = [mock_course_pref]
        mock_notif_pref_model.objects.values_list.return_value.iterator.return_value = []
        mock_notif_pref_model.objects.bulk_create.return_value = [Mock() for _ in range(4)]

        # Use StringIO to capture output
        out = StringIO()

        # This should not raise any exceptions
        call_command('migrate_preferences_to_account_level_model', '--dry-run', stdout=out)

        # Verify dry run logging was called
        self.mock_logger.info.assert_any_call("DRY RUN MODE - No changes will be made")


class MigratePreferencesToAccountLevelEdgeCasesTest(TestCase):
    """Test edge cases and error conditions."""

    def setUp(self):
        self.command = Command()
        self.command.BATCH_SIZE = 10
        self.command.CHUNK_SIZE = 5

    def test_malformed_notification_config(self):
        """Test handling of malformed notification configuration."""
        malformed_configs = [
            {'app': {'notification_types': None}},  # None notification_types
            {'app': {'notification_types': {}}},  # Empty notification_types
            {'app': {}},  # Missing notification_types
            {'app': {'notification_types': {'type': None}}},  # None values
            {'app': {'notification_types': {'type': 'string'}}},  # Non-dict values
            {'app': 'not_a_dict'},  # Non-dict app_config
            None,  # None config
        ]

        for i, config in enumerate(malformed_configs):
            with self.subTest(config=config, test_case=i):
                mock_pref = Mock()
                mock_pref.user_id = 1
                mock_pref.notification_preference_config = config

                # This should not raise any exceptions
                try:
                    result = list(self.command._generate_account_preferences([mock_pref], set()))
                    # Should handle gracefully without creating preferences
                    self.assertEqual(len(result), 0,
                                     f"Expected 0 preferences for malformed config {config}, got {len(result)}")
                except Exception as e:  # pylint: disable=broad-except
                    self.fail(f"Failed to handle malformed config {config}: {e}")

    def test_valid_notification_config_still_works(self):
        """Test that valid configurations still work after malformed config fixes."""
        valid_config = {
            'discussion': {
                'notification_types': {
                    'new_comment': {
                        'web': True,
                        'email': False,
                        'push': True,
                        'email_cadence': 'Daily'
                    }
                }
            }
        }

        mock_pref = Mock()
        mock_pref.user_id = 1
        mock_pref.notification_preference_config = valid_config

        with patch(f'{MODULE_PATH}.NotificationPreference') as mock_notif_pref:
            mock_instance = Mock()
            mock_notif_pref.return_value = mock_instance

            result = list(self.command._generate_account_preferences([mock_pref], set()))

            # Should create one preference
            self.assertEqual(len(result), 1)
            mock_notif_pref.assert_called_once_with(
                user_id=1,
                type='new_comment',
                app='discussion',
                web=True,
                email=False,
                push=True,
                email_cadence='Daily'
            )

    def test_missing_preference_values(self):
        """Test handling of missing preference values with defaults."""
        config = {
            'discussion': {
                'notification_types': {
                    'new_comment': {}  # Empty values, should use defaults
                }
            }
        }

        mock_pref = Mock()
        mock_pref.user_id = 1
        mock_pref.notification_preference_config = config

        with patch(f'{MODULE_PATH}.NotificationPreference') as mock_notif_pref:
            mock_instance = Mock()
            mock_notif_pref.return_value = mock_instance

            result = list(self.command._generate_account_preferences([mock_pref], set()))

            # Should create one preference with default values
            self.assertEqual(len(result), 1)
            mock_notif_pref.assert_called_once_with(
                user_id=1,
                type='new_comment',
                app='discussion',
                web=True,  # Default
                email=False,  # Default
                push=False,  # Default
                email_cadence='Daily'  # Default
            )
