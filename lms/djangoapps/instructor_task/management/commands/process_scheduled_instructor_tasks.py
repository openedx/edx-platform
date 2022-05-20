"""
Command to process scheduled instructor tasks.
"""
from django.core.management.base import BaseCommand

from lms.djangoapps.instructor_task.api import process_scheduled_instructor_tasks


class Command(BaseCommand):
    """
    Command to process Instructor Tasks in the `SCHEDULED` state that are due for execution.
    """
    def handle(self, *args, **options):
        process_scheduled_instructor_tasks()
