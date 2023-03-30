"""
Django admin command to save SoftwareSecurePhotoVerifications given an iterable of
verification_ids, thereby re-emitting the post_save signal.
"""

import datetime
import logging
import time

from django.core.management.base import BaseCommand

from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    This method finds those SoftwareSecurePhotoVerifications with a selected status
    from a start_datetime to an end_datetime and attempts to verify them.

    Use case: Multiple IDVs need to be resubmitted.

    Example: 
        $ ./manage.py lms trigger_softwaresecurephotoverifications_post_save_signal submitted --start_datetime="2023-03-01 00:00:00" --end_datetime="2023-03-28 23:59:59"
        (This resubmits all 'submitted' SoftwareSecurePhotoVerifications from 2023-03-01 to 2023-03-28)
    """
    help = (
        "Retries SoftwareSecurePhotoVerifications with a specified status, "
        "from a start datetime to an end datetime"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'status',
            action='store',
            nargs=1,
            type=str,
            help='SoftwareSecurePhotoVerifications status to filter for'
        )

        parser.add_argument(
            '--start_datetime',
            action='store',
            dest='start_datetime',
            help='Start date for a date range of SoftwareSecurePhotoVerifications; '
                 'Should be formatted as YYYY-mm-dd HH:MM:SS; '
                 'Requires the end_datetime arg.',
        )

        parser.add_argument(
            '--end_datetime',
            action='store',
            dest='end_datetime',
            help='End date for a date range of SoftwareSecurePhotoVerifications; '
                 'Should be formatted as YYYY-mm-dd HH:MM:SS; '
                 'Requires the start_datetime arg.',
        )

        parser.add_argument(
            '--batch_size',
            action='store',
            dest='batch_size',
            type=int,
            default=300,
            help='Maximum number of SoftwareSecurePhotoVerifications to process. '
                 'This helps avoid overloading the database while updating large amount of data.'
        )

        parser.add_argument(
            '--sleep_time',
            action='store',
            dest='sleep_time',
            type=int,
            default=10,
            help='Sleep time in seconds between update of batches'
        )

    def handle(self, *args, **options):

        status=options['status'][0]
        # Filter by status
        print("status to filter:", status)
        attempts_to_resubmit = SoftwareSecurePhotoVerification.objects.filter(
            status=status
        )
        print("RESUBMITTING:", attempts_to_resubmit)

        # Filter by date range
        # Make sure we have both a start date and end date
        try:
            start_datetime = datetime.datetime.strptime(options['start_datetime'], '%Y-%m-%d %H:%M:%S')
        except:
            log.exception("start_datetime argument not present")
            return

        try:
            end_datetime = datetime.datetime.strptime(options['end_datetime'], '%Y-%m-%d %H:%M:%S')
        except:
            log.exception("end_datetime argument not present")
            return

        attempts_to_resubmit = attempts_to_resubmit.filter(submitted_at__range=(start_datetime, end_datetime))

        log.info(
            f"Attempting to re-submit {len(attempts_to_resubmit)} failed SoftwareSecurePhotoVerification submissions; "
            f"\nIn date range: `{start_datetime}` to `{end_datetime}` with status: {status}"
        )

        batch_size = options['batch_size']
        sleep_time = options['sleep_time']
        count = 0

        # Re-submit attempts_to_resubmit
        for index, attempt in enumerate(attempts_to_resubmit):
            log.info(f"Re-submitting submission #{index} (ID: {attempt.id}, User: {attempt.user})")

            # Set the attempt's status to 'must_retry' so that we can re-submit it
            attempt.status = 'must_retry'

            attempt.submit(copy_id_photo_from=attempt.copy_id_photo_from)
            log.info(f"Retry result: {attempt.status}")
            count += 1

            # Sleep between batches of <batch_size>
            if count == batch_size:
                time.sleep(sleep_time)
                count = 0

        log.info("Done resubmitting failed photo verifications")

