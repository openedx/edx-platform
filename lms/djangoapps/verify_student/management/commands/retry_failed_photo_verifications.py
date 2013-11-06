"""
Django admin commands related to verify_student
"""

from verify_student.models import SoftwareSecurePhotoVerification
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    This method finds those PhotoVerifications with a status of
    MUST_RETRY and attempts to verify them.
    """
    help = 'Retries SoftwareSecurePhotoVerifications that are in a state of \'must_retry\''

    def handle(self, *args, **options):
        attempts_to_retry = SoftwareSecurePhotoVerification.objects.filter(status='must_retry')
        for attempt in attempts_to_retry:
            attempt.submit()
        self.stdout.write("Resubmitted failed photo verifications")
