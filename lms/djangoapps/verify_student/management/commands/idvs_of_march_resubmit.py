"""
Django admin commands related to verify_student
"""


import logging
from django.core.management.base import BaseCommand

from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification, SSPVerificationRetryConfig

log = logging.getLogger('retry_photo_verification')


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

    def add_arguments(self, parser):

        parser.add_argument(
            '--verification-ids',
            dest='verification_ids',
            action='store',
            nargs='+',
            type=str,
            help='verifications id used to retry verification'
        )

        parser.add_argument(
            '--args-from-database',
            action='store_true',
            help='Use arguments from the SSPVerificationRetryConfig model instead of the command line.',
        )

    def get_args_from_database(self):
        """ Returns an options dictionary from the current SSPVerificationRetryConfig model. """

        sspv_retry_config = SSPVerificationRetryConfig.current()
        if not sspv_retry_config.enabled:
            log.warning('SSPVerificationRetryConfig is disabled or empty, but --args-from-database was requested.')
            return {}

        # We don't need fancy shell-style whitespace/quote handling - none of our arguments are complicated
        argv = sspv_retry_config.arguments.split()

        parser = self.create_parser('manage.py', 'sspv_retry')
        return parser.parse_args(argv).__dict__  # we want a dictionary, not a non-iterable Namespace object

    def handle(self, *args, **options):

        options = self.get_args_from_database() if options['args_from_database'] else options
        args = options.get('verification_ids', None)

        if args:
            attempts_to_retry = SoftwareSecurePhotoVerification.objects.filter(
                receipt_id__in=options['verification_ids']
            )
            log.info("Fetching retry verification ids from config model")
            force_must_retry = True
        else:
            attempts_to_retry = SoftwareSecurePhotoVerification.objects.filter(status='must_retry')
            force_must_retry = False

        log.info(f"Attempting to retry {len(attempts_to_retry)} failed PhotoVerification submissions")
        for index, attempt in enumerate(attempts_to_retry):
            log.info(f"Retrying submission #{index} (ID: {attempt.id}, User: {attempt.user})")

            # Set the attempts status to 'must_retry' so that we can re-submit it
            if force_must_retry:
                attempt.status = 'must_retry'

            attempt.submit(copy_id_photo_from=attempt.copy_id_photo_from)
            log.info(f"Retry result: {attempt.status}")
        log.info("Done resubmitting failed photo verifications")
