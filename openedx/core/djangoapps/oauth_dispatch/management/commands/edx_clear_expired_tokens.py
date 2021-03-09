"""
Management command for clear expired access tokens!
"""


import logging
from datetime import timedelta
from time import sleep

from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from oauth2_provider.models import AccessToken, Grant, RefreshToken
from oauth2_provider.settings import oauth2_settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):  # lint-amnesty, pylint: disable=missing-class-docstring
    help = "Clear expired access tokens and refresh tokens for Django OAuth Toolkit"

    def add_arguments(self, parser):
        parser.add_argument('--batch_size',
                            action='store',
                            dest='batch_size',
                            type=int,
                            default=1000,
                            help='Maximum number of database rows to delete per query. '
                                 'This helps avoid locking the database when deleting large amounts of data.')
        parser.add_argument('--sleep_time',
                            action='store',
                            dest='sleep_time',
                            type=int,
                            default=10,
                            help='Sleep time between deletion of batches')
        parser.add_argument('--excluded-application-ids',
                            action='store',
                            dest='excluded-application-ids',
                            type=str,
                            default='',
                            help='Comma-separated list of application IDs for which tokens will NOT be removed')

    def clear_table_data(self, query_set, batch_size, model, sleep_time):  # lint-amnesty, pylint: disable=missing-function-docstring
        message = f'Cleaning {query_set.count()} rows from {model.__name__} table'
        logger.info(message)
        while query_set.exists():
            qs = query_set[:batch_size]
            batch_ids = qs.values_list('id', flat=True)
            with transaction.atomic():
                model.objects.filter(pk__in=list(batch_ids)).delete()

            if query_set.exists():
                sleep(sleep_time)

    def get_expiration_time(self, now):  # lint-amnesty, pylint: disable=missing-function-docstring
        refresh_token_expire_seconds = oauth2_settings.REFRESH_TOKEN_EXPIRE_SECONDS
        if not isinstance(refresh_token_expire_seconds, timedelta):
            try:
                refresh_token_expire_seconds = timedelta(seconds=refresh_token_expire_seconds)
            except TypeError:
                e = "REFRESH_TOKEN_EXPIRE_SECONDS must be either a timedelta or seconds"
                raise ImproperlyConfigured(e)  # lint-amnesty, pylint: disable=raise-missing-from
            return now - refresh_token_expire_seconds

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        sleep_time = options['sleep_time']
        if options['excluded-application-ids']:
            excluded_application_ids = [int(x) for x in options['excluded-application-ids'].split(',')]
        else:
            excluded_application_ids = []

        now = timezone.now()
        refresh_expire_at = self.get_expiration_time(now)

        query_set = RefreshToken.objects.filter(access_token__expires__lt=refresh_expire_at).exclude(
            application_id__in=excluded_application_ids)
        self.clear_table_data(query_set, batch_size, RefreshToken, sleep_time)

        query_set = AccessToken.objects.filter(refresh_token__isnull=True, expires__lt=now)
        self.clear_table_data(query_set, batch_size, AccessToken, sleep_time)

        query_set = Grant.objects.filter(expires__lt=now)
        self.clear_table_data(query_set, batch_size, Grant, sleep_time)
