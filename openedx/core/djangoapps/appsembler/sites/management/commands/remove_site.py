import traceback

from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.db import transaction

from openedx.core.djangoapps.appsembler.sites.utils import delete_site


class Command(BaseCommand):
    """
    Remove a Tahoe website from LMS records.

    Must be used `remove_site` on AMC to avoid any errors there.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--commit',
            default=False,
            dest='commit',
            help='Fully delete the site, otherwise the transaction will be rolled back.',
            action='store_true',
        )

        parser.add_argument(
            'domain',
            help='The domain of the organization to be deleted.',
            nargs='+',
            type=str,
        )

    def handle(self, *args, **options):
        domains = options['domain']

        for domain in domains:
            self.stdout.write('Removing "%s" in progress...' % domain)

            try:
                site = Site.objects.filter(domain=domain).first()
                if not site:
                    self.stderr.write(self.style.ERROR('Cannot find "{domain}"'.format(domain=domain)))
                    continue

                with transaction.atomic():
                    delete_site(site)

                    if not options['commit']:
                        transaction.set_rollback(True)
            except Exception:  # noqa
                self.stderr.write(self.style.ERROR(
                    'Failed to remove site "{domain}" error: \n {error}'.format(
                        domain=domain,
                        error=traceback.format_exc(),
                    )
                ))
                traceback.format_exc()
            else:
                self.stdout.write(self.style.SUCCESS(
                    '{message} removed site "{domain}"'.format(
                        message='Successfully' if options['commit'] else 'Dry run',
                        domain=domain,
                    )
                ))
