from django.core.management.base import BaseCommand, CommandError
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
            'domain',
            help='The domain of the organization to be deleted.',
            type=str,
        )
        parser.add_argument(
            '--commit',
            default=False,
            dest='commit',
            help='Fully delete the site, otherwise the transaction will be rolled back.',
            action='store_true',
        )

    def handle(self, *args, **options):
        organization_domain = options['domain']

        self.stdout.write('Removing "%s" in progress...' % organization_domain)
        site = self._get_site(organization_domain)

        with transaction.atomic():
            delete_site(site)

            if not options['commit']:
                transaction.set_rollback(True)

        self.stdout.write(self.style.SUCCESS(
            '{message} removed site "{domain}"'.format(
                message='Successfully' if options['commit'] else 'Dry run',
                domain=organization_domain,
            )
        ))

    def _get_site(self, domain):
        """
        Locates the site to be deleted and return its instance.

        :param domain: The domain of the site to be returned.
        :return: Returns the site object that has the given domain.
        """
        try:
            return Site.objects.get(domain=domain)
        except Site.DoesNotExist:
            raise CommandError('Cannot find "%s" in Sites!' % domain)
