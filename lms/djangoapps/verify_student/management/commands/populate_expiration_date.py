"""
Django admin command to populate expiration_date for approved verifications in SoftwareSecurePhotoVerification
"""


import logging
import time
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import F

from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification
from util.query import use_read_replica_if_available

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    This command sets the `expiration_date` for users for which the deprecated field `expiry_date` is set
    The task is performed in batches with maximum number of rows to process given in argument `batch_size`
    and a sleep time between each batch given by `sleep_time`
    Default values:
        `batch_size` = 1000 rows
        `sleep_time` = 10 seconds
    Example usage:
        $ ./manage.py lms populate_expiration_date --batch_size=1000 --sleep_time=5
    OR
        $ ./manage.py lms populate_expiration_date
    """
    help = 'Populate expiration_date for approved verifications'

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
        It filters approved Software Secure Photo Verification and then for each distinct user it finds the most
        recent approved verification and set its expiration_date
        """
        batch_size = options['batch_size']
        sleep_time = options['sleep_time']

        query = SoftwareSecurePhotoVerification.objects.filter(status='approved').order_by()
        sspv = use_read_replica_if_available(query)

        if not sspv.count():
            logger.info("No approved entries found in SoftwareSecurePhotoVerification")
            return

        distinct_user_ids = set()
        update_verification_ids = []
        update_verification_count = 0

        for verification in sspv:
            if verification.user_id not in distinct_user_ids:
                distinct_user_ids.add(verification.user_id)

                recent_verification = self.find_recent_verification(sspv, verification.user_id)
                if recent_verification.expiry_date:
                    update_verification_ids.append(recent_verification.pk)
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
        recent_verification_qs = SoftwareSecurePhotoVerification.objects.filter(pk__in=verification_ids)
        recent_verification_qs.update(expiration_date=F('expiry_date'))
        recent_verification_qs.update(expiry_date=None)

    def find_recent_verification(self, model, user_id):
        """
        Returns the most recent approved verification for a user
        """
        return model.filter(user_id=user_id).latest('updated_at')
