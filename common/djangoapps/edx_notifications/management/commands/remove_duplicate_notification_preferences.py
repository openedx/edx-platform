"""
Django management command to remove duplicate notifications preferences.
"""

import logging

from django.core.management.base import BaseCommand
from edx_notifications.stores.sql.models import (
    SQLUserNotificationPreferences,
    SQLNotificationPreference
)

log = logging.getLogger(__file__)


class Command(BaseCommand):
    """
    Django management command to remove duplicate notifications preferences.
    """

    def handle(self, *args, **options):
        """
        Management command entry point
        """

        log.info("Running management command to remove duplicate notifications preferences...")
        removed_count = 0
        preferences = SQLNotificationPreference.objects.all()
        user_ids = SQLUserNotificationPreferences.objects.values_list('user_id', flat=True)
        for user_id in user_ids:
            for preference in preferences:
                pref_count = SQLUserNotificationPreferences.objects.filter(
                    user_id=user_id, preference=preference
                ).count()
                if pref_count > 1:
                    log.info("Removing duplicate preference %s for user_id %s", preference.name, user_id)
                    try:
                        user_pref = SQLUserNotificationPreferences.objects.filter(
                            user_id=user_id, preference=preference
                        ).first()
                        SQLUserNotificationPreferences.objects.filter(
                            user_id=user_id, preference=preference
                        ).exclude(id=user_pref.id).delete()
                        removed_count += (pref_count - 1)
                    except Exception as ex:  # pylint: disable=broad-except
                        log.info(
                            "Error while removing user preference for user_id %s and preference %s %s",
                            user_id, preference.name, ex
                        )
        log.info("Total %d duplicate preferences removed", removed_count)
