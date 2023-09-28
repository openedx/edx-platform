"""
    This task will clean out the misconfigured certificate available date. When courses Change their
    certificates_display_behavior, the certificate_available_date was not updating properly. This is
    command is meant to be ran one time to clean up any courses that were not supposed to have
    certificate_available_date
"""
from django.core.management.base import BaseCommand
from openedx.core.djangoapps.credentials.tasks.v1.tasks import clean_certificate_available_date


class Command(BaseCommand):
    """
    Cleans out misconfigured certificate available dates on courses that
    are not meant to have them.
    """

    def handle(self, *args, **options):
        clean_certificate_available_date.delay()
