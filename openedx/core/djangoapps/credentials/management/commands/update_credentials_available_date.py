"""
A manangement command to populate the `certificate_available_date` field of the CourseCertificateConfiguration model in
the Credentials IDA.

This command is designed to be ran once to initially backpopulate data. Otherwise, anytime an existing course run
adjusts its certificate available date or certificates display behavior settings, updates will automatically be queued
and transmit to the Credentials IDA.
"""
from django.core.management.base import BaseCommand

from openedx.core.djangoapps.credentials.tasks.v1.tasks import backfill_date_for_all_course_runs


class Command(BaseCommand):
    """
    A management command reponsible for populating the `certificate_available_date` field of
    CourseCertificateConfiguration instances in the Credentials IDA.
    """
    def handle(self, *args, **options):
        backfill_date_for_all_course_runs.delay()
