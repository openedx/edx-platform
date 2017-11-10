"""
Django management command to raise a 'fire_background_notification_check' signal to all
application-level listeners
"""

import logging
import logging.config
import sys

# Have all logging go to stdout with management commands
# this must be up at the top otherwise the
# configuration does not appear to take affect
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
        }
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO'
    }
}
logging.config.dictConfig(LOGGING)

from django.core.management.base import BaseCommand

from edx_notifications.background import fire_background_notification_check

log = logging.getLogger(__file__)


class Command(BaseCommand):
    """
    Django Management command to force a background check of all possible notifications
    """

    def handle(self, *args, **options):
        """
        Management command entry point, simply call into the signal firiing
        """

        log.info("Running management command to fire notifications asynchronously...")

        fire_background_notification_check()

        log.info("Completed background_notification_check.")
