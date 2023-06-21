# lint-amnesty, pylint: disable=django-not-configured
"""
Management command for expiring entitlements older than 1 year / 18 months.
"""
import logging
from datetime import date
from dateutil.relativedelta import relativedelta
from math import ceil
from textwrap import dedent

from django.core.management import BaseCommand
from django.contrib.auth.models import User
from common.djangoapps.entitlements.tasks import expire_and_create_entitlements
from common.djangoapps.entitlements.models import CourseEntitlement

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

#course uuids for which entitlements should be expired after 18 months.
MIT_SUPPLY_CHAIN_COURSES = [
    '0d9b47982e3d486aa3189a7035bbda77',
    '09532745c837467b9078093b8e1265a8',
    '324970b703a444d7b39e10bbda6f119f',
    '5f1c55b4354e4155af4a76450953e10d',
    'ed927a1a4a95415ba865c3d722ac549c',
    '6513ed9c112a495182ad7036cbe52831',
]


class Command(BaseCommand):
    """
    Management command for expiring old entitlements and issuing new one against them.


    The command's goal is expire a set of entitlements depending on the --count argument passed to an
    idempotent Celery task for further (parallelized) processing.
    """
    help = dedent(__doc__).strip()

    def add_arguments(self, parser):
        parser.add_argument(
            '-c', '--commit',
            action='store_true',
            default=False,
            help='Submit tasks for processing'
        )

        parser.add_argument(
            '--count',
            type=int,
            default=100,  # arbitrary, should be adjusted if it is found to be inadequate
            help='How many entitlements to expire'
        )

        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,  # arbitrary, should be adjusted if it is found to be inadequate
            help='How many entitlements to give each celery task'
        )

    def handle(self, *args, **options):

        logger.info('Looking for entitlements which may be expirable.')

        support_user = User.objects.get(username='cbrash-edx')
        current_date = date.today()
        expiration_period = current_date - relativedelta(years=1)
        exceptional_expiration_period = current_date - relativedelta(years=1, months=6)
        normal_entitlements = CourseEntitlement.objects.filter(
            expired_at__isnull=True, created__lte=expiration_period).exclude(course_uuid__in=MIT_SUPPLY_CHAIN_COURSES)
        exceptional_entitlements = CourseEntitlement.objects.filter(
            expired_at__isnull=True, created__lte=exceptional_expiration_period, course_uuid__in=MIT_SUPPLY_CHAIN_COURSES)

        entitlements = normal_entitlements | exceptional_entitlements
        logger.info('Total entitlements that have reached expiration period are %d ', entitlements)

        entitlements_to_expire = max(1, options.get('count'))
        batch_size = max(1, options.get('batch_size'))
        num_batches = ceil(entitlements_to_expire / batch_size) if entitlements else 0

        if options.get('commit'):
            logger.info('Enqueuing %d entitlement expiration tasks.', num_batches)
        else:
            logger.info(
                'Found %d batches. To enqueue entitlement expiration tasks, pass the -c or --commit flags.',
                num_batches
            )
            return

        for batch_num in range(num_batches):
            start = batch_num * batch_size
            end = min(start + batch_size, entitlements_to_expire)
            expire_and_create_entitlements.delay(entitlements[start:end], support_user)

        logger.info('Done. Successfully enqueued %d tasks.', num_batches)
