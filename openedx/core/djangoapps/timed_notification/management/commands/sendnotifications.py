import logging

from datetime import datetime, timedelta, date
from pytz import utc

from django.core.management.base import BaseCommand, CommandError
from lms.djangoapps.branding import get_visible_courses
from openedx.core.djangoapps.timed_notification.tasks import task_course_notifications
from common.lib.mandrill_client.client import MandrillClient

log = logging.getLogger('edx.celery.task')


class Command(BaseCommand):
    """
    Command to send course reminder emails
    """
    def handle(self, *args, **options):
        task_course_notifications()
