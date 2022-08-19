"""
Migrates a Tahoe 1.0 site to have FusionAuth and Site Configuration:

 - https://appsembler.atlassian.net/wiki/spaces/RT/pages/2630352924/FusionAuth+Tahoe+Migration+Script
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from ...site_migration import migrate_site


class Command(BaseCommand):

    help = "Migrates a Tahoe 1.0 site to have FusionAuth and Site Configuration."

    def add_arguments(self, parser):
        parser.add_argument('--site-domain', required=True)
        parser.add_argument('--idp-tenant-id', required=True)
        parser.add_argument('--idp-application-id', required=True)
        parser.add_argument('--migrate-theme', choices=['true', 'false'], required=True)
        parser.add_argument(
            '--commit',
            default=False,
            dest='commit',
            help='Commit changes in the Open edX database, otherwise the transaction will be rolled back.',
            action='store_true',
        )

    def handle(self, *args, **options):
        options = {**options}  # copy to modify it freely

        # Convert `migrate_theme` to bool
        options['migrate_theme'] = options['migrate_theme'] == 'true'

        with transaction.atomic():
            migrate_site(options)

            if not options['commit']:
                transaction.set_rollback(True)
