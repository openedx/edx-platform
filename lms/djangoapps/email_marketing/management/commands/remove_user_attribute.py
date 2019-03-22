"""
Management command to remove provided user var(s) from sail-thru
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from email_marketing.tasks import update_sailthru_vars
from util.query import use_read_replica_if_available


class Command(BaseCommand):
    """
        This command removes custom attributes from user profiles on sailthru
        Example usage:
            $ ./manage.py lms remove_user_attribute --attribute=euid --chunk-size=2000
        OR
            $ ./manage.py lms remove_user_attribute --attribute=euid,grade
    """

    help = 'Removes a given user var(s) from sailthru'

    def add_arguments(self, parser):
        parser.add_argument(
            '--attribute',
            type=str,
            required=True,
            help='attribute(s) to remove from custom vars from user profile'
        )

        parser.add_argument(
            '--chunk-size',
            type=int,
            default=3000,
            help='Maximum number of users to fetch in one db call')
        pass

    def handle(self, *args, **options):
        """
        It fetches data from database in chunks and rolls celery task for each record
        """
        chunk_size = options['chunk_size']
        attribute = options['attribute']

        query = User.objects.values('email')
        queryset = use_read_replica_if_available(query)
        count = queryset.count()

        for start in range(0, count, chunk_size):
            page = queryset[start: start+chunk_size].iterator()

            for record in page:
                update_sailthru_vars.delay(record['email'], attribute)

        self.stdout.write(self.style.SUCCESS('Successfully executed management command to update custom vars on sailthru'))
