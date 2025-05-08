"""
Backfill the is_disabled attribute for existing users in Segment and Braze.

This management command identifies users with unusable passwords (starting with
UNUSABLE_PASSWORD_PREFIX) and syncs the is_disabled=true attribute to their Segment
profiles using the segment.identify() function. It processes users in
batches to minimize memory usage and supports a dry-run mode for testing.
"""

import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX
from common.djangoapps.track import segment

LOGGER = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    """
    Back fill is_disabled for users with unusable passwords in Segment.
    """
    help = 'Back fill is_disabled attribute for existing disabled users in Segment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of users to process per batch'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate the back fill without calling Segment'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        dry_run = options['dry_run']

        try:
            LOGGER.info(f"Starting back fill with batch_size={batch_size}, dry_run={dry_run}")

            queryset = User.objects.filter(
                password__startswith=UNUSABLE_PASSWORD_PREFIX
            ).values('id', 'password')

            total_users = queryset.count()
            LOGGER.info(f"Found {total_users} users that are disabled")

            if total_users == 0:
                LOGGER.info("No users to process, exiting")
                return

            processed = 0
            for user in queryset.iterator(chunk_size=batch_size):
                try:
                    if dry_run:
                        LOGGER.info(f"[Dry Run] Would update user {user['id']} with is_disabled=true")
                    else:
                        segment.identify(user['id'], {'is_disabled': 'true'})
                        LOGGER.info(f"Successfully updated user {user['id']} with is_disabled=true")
                    processed += 1
                except Exception as e:  # pylint: disable=broad-exception-caught
                    LOGGER.error(f"Failed to update user {user['id']}: {str(e)}")

            LOGGER.info(f"Back fill completed: processed {processed}/{total_users} users")

        except Exception as e:  # pylint: disable=broad-exception-caught
            LOGGER.error(f"Back fill failed: {str(e)}")
            raise
