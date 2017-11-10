"""
Django management command to force purge old notifications.
To enable this feature, the following variables have to be defined in settings:
NOTIFICATION_PURGE_READ_OLDER_THAN_DAYS
NOTIFICATION_PURGE_UNREAD_OLDER_THAN_DAYS
Optionally, the NOTIFICATION_ARCHIVE_ENABLED flag can be set to archive the purged notifications.
"""

import logging

from django.core.management.base import BaseCommand
from edx_notifications.lib.publisher import purge_expired_notifications

log = logging.getLogger(__file__)


class Command(BaseCommand):
    """
    Django Management command to force purge old notifications.
    """

    def handle(self, *args, **options):
        """
        Management command entry point, simply call into the signal firiing
        """

        log.info("Running management command to force purge old notifications...")
        purge_expired_notifications()
