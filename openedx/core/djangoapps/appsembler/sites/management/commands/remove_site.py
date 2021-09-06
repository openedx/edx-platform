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

    def handle(self, *args, **options):
        organization_domain = options['domain']
        self.stdout.write(self.style.WARNING('Same command must be ran on the connected AMC instance'))

        self.stdout.write('Removing "%s" in progress...' % organization_domain)
        organization = self._get_site(organization_domain)

        with transaction.atomic():
            delete_site(organization)

        self.stdout.write(self.style.SUCCESS('Successfully removed site "%s"' % organization_domain))

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
