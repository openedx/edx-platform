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
        print("Attempting to retry {0} failed PhotoVerification submissions".format(len(attempts_to_retry)))
        for index, attempt in enumerate(attempts_to_retry):
            print("Retrying submission #{0} (ID: {1}, User: {2})".format(index, attempt.id, attempt.user))
            attempt.submit()
            print("Retry result: {0}".format(attempt.status))
        print("Done resubmitting failed photo verifications")
