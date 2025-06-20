"""
Command to migrate course-level notification preferences to account-level preferences.
"""
import logging
from typing import Dict, List, Any, Iterator
from collections import defaultdict

from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

from openedx.core.djangoapps.notifications.email_notifications import EmailCadence
from openedx.core.djangoapps.notifications.models import CourseNotificationPreference, NotificationPreference
from openedx.core.djangoapps.notifications.utils import aggregate_notification_configs

logger = logging.getLogger(__name__)

DEFAULT_BATCH_SIZE = 1000


class Command(BaseCommand):
    """
    Migrates course-level notification preferences to account-level notification preferences.

    This command processes users in batches, aggregates their course-level preferences,
    and creates new account-level preferences. It includes a dry-run mode.
    Existing account-level preferences for a processed user will be deleted before
    new ones are created to ensure idempotency.
    """
    help = "Migrates course-level notification preferences to account-level preferences for all relevant users."

    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=DEFAULT_BATCH_SIZE,
            help=f"The number of users to process in each batch. Default: {DEFAULT_BATCH_SIZE}"
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Simulate the migration without making any database changes."
        )

    @staticmethod
    def _get_user_ids_to_process() -> Iterator[int]:
        """
        Yields all distinct user IDs with course notification preferences.
        """
        logger.info("Fetching all distinct user IDs with course notification preferences...")
        user_id_queryset = (CourseNotificationPreference
                            .objects
                            .values_list('user_id', flat=True)
                            .distinct())
        # The iterator with chunk_size is memory efficient for fetching the IDs themselves.
        yield from user_id_queryset.iterator()

    @staticmethod
    def _create_preference_object(
        user_id: int,
        app_name: str,
        notification_type: str,
        values: Dict[str, Any]
    ) -> NotificationPreference:
        """
        Helper function to create a NotificationPreference instance.
        """
        return NotificationPreference(
            user_id=user_id,
            app=app_name,
            type=notification_type,
            web=values.get('web'),
            email=values.get('email'),
            push=values.get('push'),
            email_cadence=values.get('email_cadence', EmailCadence.DAILY)
        )

    def _create_preferences_from_configs(
        self,
        user_id: int,
        course_preferences_configs: List[Dict]
    ) -> List[NotificationPreference]:
        """
        Processes a list of preference configs for a single user.
        Returns a list of NotificationPreference objects to be created.
        """
        new_account_preferences: List[NotificationPreference] = []

        if not course_preferences_configs:
            logger.debug(f"No course preferences found for user {user_id}. Skipping.")
            return new_account_preferences

        aggregated_data = aggregate_notification_configs(course_preferences_configs)

        for app_name, app_config in aggregated_data.items():
            if not isinstance(app_config, dict):
                logger.warning(
                    f"Malformed app_config for app '{app_name}' for user {user_id}. "
                    f"Expected dict, got {type(app_config)}. Skipping app."
                )
                continue

            notif_types = app_config.get('notification_types', {})
            if not isinstance(notif_types, dict):
                logger.warning(
                    f"Malformed 'notification_types' for app '{app_name}' for user {user_id}. Expected dict, "
                    f"got {type(notif_types)}. Skipping notification_types."
                )
                continue

            # Handle regular notification types
            for notification_type, values in notif_types.items():
                if notification_type == 'core':
                    continue
                if values is None or not isinstance(values, dict):
                    logger.warning(
                        f"Skipping malformed notification type data for '{notification_type}' "
                        f"in app '{app_name}' for user {user_id}."
                    )
                    continue
                new_account_preferences.append(
                    self._create_preference_object(user_id, app_name, notification_type, values)
                )

            # Handle core notification types
            core_types_list = app_config.get('core_notification_types', [])
            if not isinstance(core_types_list, list):
                logger.warning(
                    f"Malformed 'core_notification_types' for app '{app_name}' for user {user_id}. "
                    f"Expected list, got {type(core_types_list)}. Skipping core_notification_types."
                )
                continue

            core_values = notif_types.get('core', {})
            if not isinstance(core_values, dict):
                logger.warning(
                    f"Malformed values for 'core' notification types in app '{app_name}' for user {user_id}. "
                    f"Expected dict, got {type(core_values)}. Using empty defaults."
                )
                core_values = {}

            for core_type_name in core_types_list:
                if core_type_name is None or not isinstance(core_type_name, str):
                    logger.warning(
                        f"Skipping malformed core_type_name: '{core_type_name}' in app '{app_name}' for user {user_id}."
                    )
                    continue
                new_account_preferences.append(
                    self._create_preference_object(user_id, app_name, core_type_name, core_values)
                )
        return new_account_preferences

    def _process_batch(self, user_ids: List[int]) -> List[NotificationPreference]:
        """
        Fetches all preferences for a batch of users and processes them.
        """
        all_new_preferences: List[NotificationPreference] = []

        # 1. Fetch all preference data for the batch in a single query.
        course_prefs = CourseNotificationPreference.objects.filter(
            user_id__in=user_ids
        ).values('user_id', 'notification_preference_config')

        # 2. Group the fetched data by user_id in memory.
        prefs_by_user = defaultdict(list)
        for pref in course_prefs:
            prefs_by_user[pref['user_id']].append(pref['notification_preference_config'])

        # 3. Process each user's grouped data.
        for user_id, configs in prefs_by_user.items():
            user_new_preferences = self._create_preferences_from_configs(user_id, configs)
            if user_new_preferences:
                all_new_preferences.extend(user_new_preferences)
                logger.debug(f"User {user_id}: Aggregated {len(configs)} course preferences "
                             f"into {len(user_new_preferences)} account preferences.")
            else:
                logger.debug(f"User {user_id}: No account preferences generated from {len(configs)} "
                             f"course preferences.")

        return all_new_preferences

    def handle(self, *args: Any, **options: Any):
        dry_run = options['dry_run']
        batch_size = options['batch_size']

        if dry_run:
            logger.info(self.style.WARNING("Performing a DRY RUN. No changes will be made to the database."))
        else:
            # Clear all existing preferences once at the beginning.
            # This is more efficient and safer than deleting per-user.
            NotificationPreference.objects.all().delete()
            logger.info('Cleared all existing account-level notification preferences.')

        user_id_iterator = self._get_user_ids_to_process()

        user_id_batch: List[int] = []
        total_users_processed = 0
        total_preferences_created = 0

        for user_id in user_id_iterator:
            user_id_batch.append(user_id)

            if len(user_id_batch) >= batch_size:
                try:
                    with transaction.atomic():
                        # Process the entire batch of users
                        preferences_to_create = self._process_batch(user_id_batch)

                        if preferences_to_create:
                            if not dry_run:
                                NotificationPreference.objects.bulk_create(preferences_to_create)

                            total_preferences_created += len(preferences_to_create)
                            logger.info(
                                self.style.SUCCESS(
                                    f"Batch complete. {'Would create' if dry_run else 'Created'} "
                                    f"{len(preferences_to_create)} preferences for {len(user_id_batch)} users."
                                )
                            )
                        else:
                            logger.info(f"Batch complete. No preferences to create for {len(user_id_batch)} users.")

                        total_users_processed += len(user_id_batch)
                        user_id_batch = []  # Reset the batch

                except Exception as e:  # pylint: disable=broad-except
                    logger.error(f"Failed to process batch containing users {user_id_batch}: {e}", exc_info=True)
                    # The transaction for the whole batch will be rolled back.
                    # Clear the batch to continue with the next set of users.
                    user_id_batch = []

                if total_users_processed > 0 and total_users_processed % (batch_size * 5) == 0:
                    logger.info(f"PROGRESS: Total users processed so far: {total_users_processed}. "
                                f"Total preferences {'would be' if dry_run else ''} "
                                f"created: {total_preferences_created}")

        # Process any remaining users in the last, smaller batch
        if user_id_batch:
            try:
                with transaction.atomic():
                    preferences_to_create = self._process_batch(user_id_batch)
                    if preferences_to_create:
                        if not dry_run:
                            NotificationPreference.objects.bulk_create(preferences_to_create)
                        total_preferences_created += len(preferences_to_create)
                        logger.info(
                            self.style.SUCCESS(
                                f"Final batch complete. {'Would create' if dry_run else 'Created'} "
                                f"{len(preferences_to_create)} preferences for {len(user_id_batch)} users."
                            )
                        )
                    total_users_processed += len(user_id_batch)
            except Exception as e:  # pylint: disable=broad-except
                logger.error(f"Failed to process final batch of users {user_id_batch}: {e}", exc_info=True)

        logger.info(
            self.style.SUCCESS(
                f"Migration complete. Processed {total_users_processed} users. "
                f"{'Would have created' if dry_run else 'Created'} a total of {total_preferences_created} "
                f"account-level preferences."
            )
        )
        if dry_run:
            logger.info(self.style.WARNING("DRY RUN finished. No actual changes were made."))
