"""
Django admin commands related to populating existing verifications (including
SoftwareSecurePhotoVerification and SSOVerifications).
"""

import logging
import time

from itertools import chain
from celery import task
from celery_utils.persist_on_failure import LoggedPersistOnFailureTask
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError

from lms.djangoapps.verify_student.models import (
    IDVerificationAggregate,
    SoftwareSecurePhotoVerification,
    SSOVerification
)

log = logging.getLogger(__name__)

DEFAULT_ALL_VERIFICATION_ATTEMPTS = True
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_SLEEP_BETWEEN_TIME = 0.0

def chunks(sequence, chunk_size):
    return (sequence[index: index + chunk_size] for index in xrange(0, len(sequence), chunk_size))

class Command(BaseCommand):
    """
    This command finds existing verifications and attempts to populate IDVerificationAggregate.
    """
    args = "<SoftwareSecurePhotoVerification id, SSOVerification id, ...>"
    help = (
        "Populates IDVerificationAggregate with existing SoftwareSecurePhotoVerifications "
        "and SSOVerifications passed as arguments, or if no arguments are supplied, all existing "
        "verifications."
    )

    def add_arguments(self, parser):
        """
        Add arguments to the command parser.
        """
        parser.add_argument(
            '--all-attempts', '--all',
            dest='all_attempts',
            action='store_true',
            default=DEFAULT_ALL_VERIFICATION_ATTEMPTS,
            help=u'Copy all verification attempts.',
        )

        parser.add_argument(
            '--chunk-size',
            dest='chunk_size',
            action='store',
            type=int,
            default=DEFAULT_CHUNK_SIZE,
            help=u'The maximum number of verification attempts to process in a single transaction.'
        )

        parser.add_argument(
            '--sleep-between',
            dest='sleep_between',
            action='store',
            type=float,
            default=DEFAULT_SLEEP_BETWEEN_TIME,
            help=u'The amount of time to sleep (in seconds) between transactions.'
        )

    def handle(self, *args, **options):
        """
        Example usage:
        $ ./manage.py lms populate_id_verification_aggregate --settings=devstack --all-attempts --chunk-size=1000
        """
        if not options.get('all_attempts') and len(args) < 1:
            raise CommandError('At least one verification attempt or --all-attempts must be specified.')

        kwargs = {}
        for key in ('all_attempts', 'chunk_size', 'sleep_between'):
            if options.get(key):
                kwargs[key] = options[key]

        try:
            enqueue_async_populate_id_verification_aggregate_tasks(
                attempt_ids=args,
                **kwargs
            )
        except Exception as exc:
            raise CommandError(u'Oh no, an error occurred: ' + unicode(exc))

def enqueue_async_populate_id_verification_aggregate_tasks(
    attempt_ids,
    all_attempts=False,
    chunk_size=DEFAULT_CHUNK_SIZE,
    sleep_between=DEFAULT_SLEEP_BETWEEN_TIME
):
    if all_attempts:
        software_secure_verifications = SoftwareSecurePhotoVerification.objects.all()
        sso_verifications = SSOVerification.objects.all()
    else:
        # TODO how can we support passing in the id's of verification attempts we want
        # from both SoftwareSecurePhotoVerification AND SSOVerifications
        software_secure_verifications = SoftwareSecurePhotoVerification.objects.filter(
            id__in=attempt_ids
        )
        sso_verifications = SSOVerification.objects.filter(
            id__in=attempt_ids
        )

    verification_attempts = [attempt for attempt in chain(software_secure_verifications, sso_verifications)]

    log.info("Attempting to copy {0} verification submissions...".format(len(verification_attempts)))
    for verification_attempts_group in chunks(verification_attempts, chunk_size):
        async_populate_id_verification_aggregate.apply_async(
            args=verification_attempts_group
        )
        log.info("Sleeping %s seconds...", sleep_between)
        time.sleep(sleep_between)

    log.info("Hooray, we're done iterating through all chunks!")

@task(base=LoggedPersistOnFailureTask)
def async_populate_id_verification_aggregate(*args, **kwargs):
    # Iterate through each attempt in the chunk
    for attempt in args:
        log.info("Copying submission attempt - ID: {1}, User: {2})".format(
            attempt.id, attempt.user
        ))
        content_type = ContentType.objects.get_for_model(attempt)
        IDVerificationAggregate.objects.create(
            status=attempt.status,
            user=attempt.user,
            name=attempt.name,
            created_at=attempt.created_at,
            updated_at=attempt.updated_at,
            content_type=content_type,
            object_id=attempt.id,
        )