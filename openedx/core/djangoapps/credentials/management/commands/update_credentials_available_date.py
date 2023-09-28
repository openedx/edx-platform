"""
A manangement command to populate the new available_date field in all CourseCertificates
in credentials. Accomplished by sending the COURSE_CERT_DATE_CHANGE signal accross all
course runs in the LMS to call a new API in credentials that will populate the date if one
is found.

This command is designed to be ran once to backpopulate data. New courses added or any time
the COURSE_CERT_DATE_CHANGE signal fires, the API will automatically be called as a part of
that flow.
"""
from django.core.management.base import BaseCommand

from openedx.core.djangoapps.credentials.tasks.v1.tasks import backfill_date_for_all_course_runs


class Command(BaseCommand):
    """
    A command to populate the available_date field in the CourseCertificate model for every
    course run inside of the LMS.
    """

    def handle(self, *args, **options):
        backfill_date_for_all_course_runs.delay()
