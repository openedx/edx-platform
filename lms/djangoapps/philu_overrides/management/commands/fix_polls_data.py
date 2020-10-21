"""
PhilU overrides the `fix_polls_data` management command
"""
import logging

from django.core.management.base import BaseCommand

from lms.djangoapps.philu_overrides.courseware.tasks import task_correct_polls_data

log = logging.getLogger('edx.celery.task')


class Command(BaseCommand):
    """
    Command to fix data poll's possible choices
    """
    def handle(self, *args, **options):
        task_correct_polls_data()
