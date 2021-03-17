"""
Django admin command to update expiration_date for approved verifications in SoftwareSecurePhotoVerification
"""


import logging
import time
from datetime import timedelta  # lint-amnesty, pylint: disable=unused-import

from django.conf import settings  # lint-amnesty, pylint: disable=unused-import
from django.core.management.base import BaseCommand
from django.db.models import F

from common.djangoapps.util.query import use_read_replica_if_available
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    This command updates the `expiration_date` for old entries still dependent on `expiry_date`
    The task is performed in batches with maximum number of rows to process given in argument `batch_size`
    and a sleep time between each batch given by `sleep_time`
    Default values:
        `batch_size` = 1000 rows
        `sleep_time` = 10 seconds
    Example usage:
        $ ./manage.py lms update_expiration_date --batch_size=1000 --sleep_time=5
    OR
        $ ./manage.py lms update_expiration_date
    """
    help = 'Update expiration_date for approved verifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch_size',
            action='store',
            dest='batch_size',
            type=int,
            default=1000,
            help='Maximum number of database rows to process. '
                 'This helps avoid locking the database while updating large amount of data.')
        parser.add_argument(
            '--sleep_time',
            action='store',
            dest='sleep_time',
            type=int,
            default=10,
            help='Sleep time in seconds between update of batches')

    def handle(self, *args, **options):
        """
        Handler for the command
        It filters approved Software Secure Photo Verifications and then sets the correct expiration_date
        """
        batch_size = options['batch_size']
        sleep_time = options['sleep_time']

        query = SoftwareSecurePhotoVerification.objects.filter(status='approved').order_by()
        sspv = use_read_replica_if_available(query)

        if not sspv.count():
            logger.info("No approved entries found in SoftwareSecurePhotoVerification")
            return

        update_verification_ids = []
        update_verification_count = 0

        for verification in sspv:
            # The expiration date should not be higher than 365 days
            # past the `updated_at` field, so only update those entries
            if verification.expiration_date > (
                verification.updated_at + timedelta(days=settings.VERIFY_STUDENT["DAYS_GOOD_FOR"])
            ):
                update_verification_ids.append(verification.pk)
                update_verification_count += 1

            if update_verification_count == batch_size:
                self.bulk_update(update_verification_ids)
                update_verification_count = 0
                update_verification_ids = []
                time.sleep(sleep_time)

        if update_verification_ids:
            self.bulk_update(update_verification_ids)

    def bulk_update(self, verification_ids):
        """
        It updates the expiration_date and sets the expiry_date to NULL for all the
        verifications whose ids lie in verification_ids
        """
        verification_qs = SoftwareSecurePhotoVerification.objects.filter(pk__in=verification_ids)
        verification_qs.update(expiration_date=F('created_at') + timedelta(
            days=settings.VERIFY_STUDENT["DAYS_GOOD_FOR"]))
        verification_qs.update(expiry_date=None)
