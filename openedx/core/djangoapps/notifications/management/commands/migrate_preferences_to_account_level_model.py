"""
Migration command for course level notification preferences to account level preferences.
"""
import logging
from typing import Dict, List, Any

from django.core.management.base import BaseCommand
from django.db import transaction

from openedx.core.djangoapps.notifications.models import CourseNotificationPreference, NotificationPreference

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
     Preference migration command.

    Invoke with:
        python manage.py [lms|cms] migrate_preferences_to_account_level ...

    Key optimizations:
    - Pre-fetch existing preferences to avoid conflicts
    - Use set operations for deduplication
    - Minimize database queries with efficient batching
    - Better memory management with generator pattern
    - Enhanced error handling and progress reporting
    """

    BATCH_SIZE = 10000  # Increased for better throughput
    CHUNK_SIZE = 1000  # Process preferences in smaller chunks

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without making changes'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=self.BATCH_SIZE,
            help=f'Batch size for bulk operations (default: {self.BATCH_SIZE})'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        batch_size = options.get('batch_size', self.BATCH_SIZE)

        if dry_run:
            logger.info("DRY RUN MODE - No changes will be made")

        # Get total count for progress tracking
        total_course_prefs = CourseNotificationPreference.objects.count()
        logger.info("Starting migration of %d course-level preferences", total_course_prefs)

        # Pre-fetch existing account-level preferences to avoid conflicts
        existing_prefs = self._get_existing_preferences()
        logger.info("Found %d existing account-level preferences", len(existing_prefs))

        processed_count = 0
        created_count = 0

        # Process in chunks to manage memory
        for chunk in self._get_preference_chunks():
            new_preferences = list(self._generate_account_preferences(chunk, existing_prefs))

            if new_preferences and not dry_run:
                created_batch = self._bulk_create_preferences(new_preferences, batch_size)
                created_count += created_batch
            elif dry_run:
                created_count += len(new_preferences)
                logger.info("DRY RUN: Would create %d preferences from this chunk", len(new_preferences))

            processed_count += len(chunk)

            if processed_count % (self.CHUNK_SIZE * 5) == 0:
                logger.info("Progress: %d/%d course preferences processed, %d account preferences created",
                            processed_count, total_course_prefs, created_count)

        logger.info("Migration complete: processed %d course preferences, created %d account preferences",
                    processed_count, created_count)

    def _get_existing_preferences(self) -> set:
        """Pre-fetch existing preferences to avoid conflicts efficiently."""
        existing = NotificationPreference.objects.values_list(
            'user_id', 'type', 'app'
        ).iterator(chunk_size=self.BATCH_SIZE)

        return set(existing)

    def _get_preference_chunks(self):
        """Generator that yields chunks of CourseNotificationPreference objects."""
        queryset = CourseNotificationPreference.objects.only(
            'user_id', 'notification_preference_config'
        ).iterator(chunk_size=self.CHUNK_SIZE)

        chunk = []
        for pref in queryset:
            chunk.append(pref)
            if len(chunk) >= self.CHUNK_SIZE:
                yield chunk
                chunk = []

        if chunk:
            yield chunk

    def _generate_account_preferences(self, course_prefs: List, existing_prefs: set):
        """Generate NotificationPreference instances from course preferences."""
        seen_in_batch = set()  # Track duplicates within current batch

        for pref in course_prefs:
            config = pref.notification_preference_config or {}

            # Ensure config is a dictionary
            if not isinstance(config, dict):
                continue

            for app_name, app_config in config.items():
                if not isinstance(app_config, dict):
                    continue

                notif_types = app_config.get('notification_types', {})
                if not isinstance(notif_types, dict):
                    continue

                for notification_type, values in notif_types.items():
                    # Skip if values is None or not a dict (malformed data)
                    if values is None or not isinstance(values, dict):
                        continue

                    # Handle core notification types expansion
                    types_to_process = self._expand_notification_types(
                        notification_type, app_config
                    )

                    for final_type in types_to_process:
                        pref_key = (pref.user_id, final_type, app_name)

                        # Skip if already exists or seen in this batch
                        if pref_key in existing_prefs or pref_key in seen_in_batch:
                            continue

                        seen_in_batch.add(pref_key)

                        yield NotificationPreference(
                            user_id=pref.user_id,
                            type=final_type,
                            app=app_name,
                            web=values.get('web', True),
                            email=values.get('email', False),
                            push=values.get('push', False),
                            email_cadence=values.get('email_cadence', 'Daily'),
                        )

    def _expand_notification_types(self, notification_type: str, app_config: Dict[str, Any]) -> List[str]:
        """Expand core notification types or return single type."""
        if notification_type == 'core':
            return app_config.get('core_notification_types', [])
        return [notification_type]

    def _bulk_create_preferences(self, preferences: List[NotificationPreference], batch_size: int) -> int:
        """Bulk create preferences with optimized error handling."""
        if not preferences:
            return 0

        created_count = 0

        # Process in batches to avoid memory issues
        for i in range(0, len(preferences), batch_size):
            batch = preferences[i:i + batch_size]

            try:
                with transaction.atomic():
                    created_objects = NotificationPreference.objects.bulk_create(
                        batch,
                        batch_size=batch_size,
                        ignore_conflicts=True
                    )
                    batch_created = len(created_objects) if hasattr(created_objects, '__len__') else len(batch)
                    created_count += batch_created

            except Exception as e:  # pylint: disable=broad-except
                logger.error("Bulk create failed for batch of %d items: %s", len(batch), str(e))
                # Try individual inserts as fallback
                created_count += self._fallback_individual_create(batch)

        return created_count

    def _fallback_individual_create(self, preferences: List[NotificationPreference]) -> int:
        """Fallback to individual creation if bulk_create fails."""
        created_count = 0

        for pref in preferences:
            try:
                pref.save()
                created_count += 1
            except Exception as e:  # pylint: disable=broad-except
                logger.warning(
                    "Failed to create individual preference for user %d: %s",
                    pref.user_id, str(e)
                )

        logger.info(
            "Fallback creation completed: %d/%d preferences created",
            created_count, len(preferences)
        )
        return created_count
