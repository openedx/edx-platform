"""
Management command for deleting expired notifications
"""
from django.core.management.base import BaseCommand

from openedx.core.djangoapps.notifications.tasks import delete_expired_notifications


class Command(BaseCommand):
    """
    Invoke with:

        python manage.py lms delete_expired_notifications
    """
    help = (
        "Deletes notifications that have been expired"
    )

    def handle(self, *args, **kwargs):
        delete_expired_notifications.delay()
