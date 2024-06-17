"""
A manangement command to populate or correct the `certificate_available_date` data of the
CourseCertificateConfiguration model instances stored by the Credentials IDA.
"""
from django.core.management.base import BaseCommand

from openedx.core.djangoapps.credentials.tasks.v1.tasks import backfill_date_for_all_course_runs


class Command(BaseCommand):
    """
    Enqueue the `backfill_date_for_all_course_runs` Celery task, which will enqueue additional subtasks responsible for
    sending certificate availability updates to the Credentials IDA.

    Example usage:
        $ ./manage.py lms update_credentials_available_date
    """
    def handle(self, *args, **options):
        backfill_date_for_all_course_runs.delay()
