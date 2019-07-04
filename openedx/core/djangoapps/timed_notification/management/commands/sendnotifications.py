import logging

from django.core.management.base import BaseCommand
from openedx.core.djangoapps.timed_notification.tasks import task_course_notifications

log = logging.getLogger('edx.celery.task')


class Command(BaseCommand):
    """
    Command to send course reminder emails
    """
    def handle(self, *args, **options):
        task_course_notifications()
