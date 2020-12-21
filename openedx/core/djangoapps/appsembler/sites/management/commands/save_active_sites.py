from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from openedx.core.djangoapps.appsembler.sites.utils import get_active_sites
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration


class Command(BaseCommand):
    """
    Save all active sites to refresh CSS as a side effect.

    This command is useful after deployments.
    """

    help = "Force save on active site configurations"

    def handle(self, *args, **options):
        if not settings.ROOT_URLCONF == 'lms.urls':
            raise CommandError('This command can only be run from within the LMS')
        for site in get_active_sites():
            print('On:', site.domain)
            try:
                site_config = SiteConfiguration.objects.get(site=site)
                site_config.save()
                print('OK')
            except Exception as e:
                print('Error')
                print(e)
