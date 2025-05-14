"""
Backfill the is_disabled attribute for existing users in Segment and Braze.

This management command identifies users with unusable passwords (starting with
UNUSABLE_PASSWORD_PREFIX) and syncs the is_disabled=true attribute to their Segment
profiles using the segment.identify() function. It processes users in
batches to minimize memory usage and supports a dry-run mode for testing.
"""

import logging
import time
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX
from django.db import DatabaseError
from common.djangoapps.track import segment
import requests

LOGGER = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    """Backfill is_disabled attribute for users with unusable passwords in Segment."""
    help = 'Backfill is_disabled for disabled users in Segment'

    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=9000, help='Users per batch')
        parser.add_argument('--dry-run', action='store_true', help='Simulate without calling Segment')
        parser.add_argument('--retry-limit', type=int, default=3, help='Retry attempts for failed API calls')

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        retry_limit = options['retry_limit']

        try:
            LOGGER.info(f"Starting backfill (batch_size={batch_size}, dry_run={dry_run}, retry_limit={retry_limit})")

            total_users = User.objects.filter(password__startswith=UNUSABLE_PASSWORD_PREFIX).count()

            if total_users == 0:
                LOGGER.info("No users to process")
                return

            LOGGER.info(f"Found {total_users} disabled users")

            offset = 0
            processed = 0
            batch_number = 0

            while offset < total_users:
                batch_number += 1
                users_batch = User.objects.filter(
                    password__startswith=UNUSABLE_PASSWORD_PREFIX
                ).values_list('id', flat=True)[offset:offset+batch_size]
                current_batch_size = len(users_batch)

                LOGGER.info(f"Processing batch {batch_number} ({current_batch_size} users)")

                if dry_run:
                    for user_id in users_batch:
                        LOGGER.info(f"[Dry Run] Would update user {user_id} with is_disabled=true in batch {batch_number}")
                    processed += current_batch_size
                else:
                    retry_count = 0
                    success = False

                    while not success and retry_count <= retry_limit:
                        try:
                            for user_id in users_batch:
                                try:
                                    segment.analytics.identify(user_id=user_id, traits={'is_disabled': True})
                                    LOGGER.info(f"Successfully updated user {user_id} with is_disabled=true in batch {batch_number}")
                                except (ConnectionError, ValueError) as e:
                                    LOGGER.error(f"Failed to update user {user_id} in batch {batch_number}: {str(e)}")
                            segment.analytics.flush()
                            LOGGER.info(f"Successfully processed batch {batch_number}")
                            success = True
                            processed += current_batch_size
                        except (requests.exceptions.RequestException, segment.analytics.errors.APIError) as e:
                            retry_count += 1
                            if retry_count <= retry_limit:
                                LOGGER.warning(f"Batch {batch_number} failed (attempt {retry_count}/{retry_limit}): {str(e)}")
                                time.sleep(2 * retry_count)
                            else:
                                LOGGER.error(f"Batch {batch_number} failed after {retry_limit} attempts, processed {processed} users: {str(e)}")
                                return

                offset += batch_size
                LOGGER.info(f"Processed {processed}/{total_users} users")

            LOGGER.info(f"Completed: processed {processed}/{total_users} users in {batch_number} batches")

        except DatabaseError as e:
            LOGGER.error(f"Back fill failed: {str(e)}")
