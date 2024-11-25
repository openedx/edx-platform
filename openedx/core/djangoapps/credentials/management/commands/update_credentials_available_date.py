"""
<<<<<<< HEAD
A manangement command to populate the `certificate_available_date` field of the CourseCertificateConfiguration model in
the Credentials IDA.

This command is designed to be ran once to initially backpopulate data. Otherwise, anytime an existing course run
adjusts its certificate available date or certificates display behavior settings, updates will automatically be queued
and transmit to the Credentials IDA.
=======
A manangement command to populate or correct the `certificate_available_date` data of the
CourseCertificateConfiguration model instances stored by the Credentials IDA.
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
"""
from django.core.management.base import BaseCommand

from openedx.core.djangoapps.credentials.tasks.v1.tasks import backfill_date_for_all_course_runs


class Command(BaseCommand):
    """
<<<<<<< HEAD
    A management command reponsible for populating the `certificate_available_date` field of
    CourseCertificateConfiguration instances in the Credentials IDA.
=======
    Enqueue the `backfill_date_for_all_course_runs` Celery task, which will enqueue additional subtasks responsible for
    sending certificate availability updates to the Credentials IDA.

    Example usage:
        $ ./manage.py lms update_credentials_available_date
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    """
    def handle(self, *args, **options):
        backfill_date_for_all_course_runs.delay()
