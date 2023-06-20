# lint-amnesty, pylint: disable=django-not-configured
"""
Management command for expiring old entitlements.
"""


import logging
from textwrap import dedent

from django.core.management import BaseCommand

from common.djangoapps.entitlements.tasks import expire_and_create_entitlements

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


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

        total = max(1, options.get('count'))
        batch_size = max(1, options.get('batch_size'))
        num_batches = ((total - 1) / batch_size + 1) if total > 0 else 0

        if options.get('commit'):
            logger.info('Enqueuing %d entitlement expiration tasks.', num_batches)
        else:
            logger.info(
                'Found %d batches. To enqueue entitlement expiration tasks, pass the -c or --commit flags.',
                num_batches
            )
            return

        while total > 0:
            total = total - batch_size
            no_of_entitlements = min(total, batch_size)
            expire_and_create_entitlements.delay(no_of_entitlements)

        logger.info('Done. Successfully enqueued %d tasks.', num_batches)
