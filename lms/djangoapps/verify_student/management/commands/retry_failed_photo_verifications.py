"""
Django admin commands related to verify_student
"""

from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    This method finds those PhotoVerifications with a status of
    MUST_RETRY and attempts to verify them.
    """
    args = "<SoftwareSecurePhotoVerification id, SoftwareSecurePhotoVerification id, ...>"
    help = (
        "Retries SoftwareSecurePhotoVerifications passed as "
        "arguments, or if no arguments are supplied, all that "
        "are in a state of 'must_retry'"
    )

    def handle(self, *args, **options):
        if args:
            attempts_to_retry = SoftwareSecurePhotoVerification.objects.filter(
                receipt_id__in=args
            )
            force_must_retry = True
        else:
            attempts_to_retry = SoftwareSecurePhotoVerification.objects.filter(status='must_retry')
            force_must_retry = False

        print "Attempting to retry {0} failed PhotoVerification submissions".format(len(attempts_to_retry))
        for index, attempt in enumerate(attempts_to_retry):
            print "Retrying submission #{0} (ID: {1}, User: {2})".format(index, attempt.id, attempt.user)

            # Set the attempts status to 'must_retry' so that we can re-submit it
            if force_must_retry:
                attempt.status = 'must_retry'

            attempt.submit(copy_id_photo_from=attempt.copy_id_photo_from)
            print "Retry result: {0}".format(attempt.status)
        print "Done resubmitting failed photo verifications"
