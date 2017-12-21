"""
Management command for expiring old entitlements.
"""

import logging

from django.core.management import BaseCommand
from django.core.paginator import Paginator

from entitlements.models import CourseEntitlement
from entitlements.tasks.v1.tasks import expire_old_entitlements

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class Command(BaseCommand):
    """
    Management command for expiring old entitlements.

    Most entitlements get expired as the user interacts with the platform,
    because the LMS checks as it goes. But if the learner has not logged in
    for a while, we still want to reap these old entitlements. So this command
    should be run every now and then (probably daily) to expire old
    entitlements.

    The command's goal is to pass a narrow subset of entitlements to an
    idempotent Celery task for further (parallelized) processing.
    """
    help = 'Expire old entitlements.'

    def add_arguments(self, parser):
        parser.add_argument(
            '-c', '--commit',
            action='store_true',
            default=False,
            help='Submit tasks for processing'
        )

        parser.add_argument(
            '--batch-size',
            type=int,
            default=10000,  # arbitrary, should be adjusted if it is found to be inadequate
            help='How many entitlements to give each celery task'
        )

    def handle(self, *args, **options):
        logger.info('Looking for entitlements which may be expirable.')

        # This query could be optimized to return a more narrow set, but at a
        # complexity cost. See bug LEARNER-3451 about improving it.
        entitlements = CourseEntitlement.objects.filter(expired_at__isnull=True).order_by('id')

        batch_size = max(1, options.get('batch_size'))
        entitlements = Paginator(entitlements, batch_size, allow_empty_first_page=False)

        if options.get('commit'):
            logger.info('Enqueuing entitlement expiration tasks for %d candidates.', entitlements.count)
        else:
            logger.info(
                'Found %d candidates. To enqueue entitlement expiration tasks, pass the -c or --commit flags.',
                entitlements.count
            )
            return

        for page_num in entitlements.page_range:
            page = entitlements.page(page_num)
            expire_old_entitlements.delay(page, logid=str(page_num))

        logger.info('Done. Successfully enqueued tasks.')
