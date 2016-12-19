import sys

from django.contrib.sites.models import Site
from django.conf import settings
from django.core.management.base import NoArgsCommand


from openedx.core.djangoapps.site_configuration.models import SiteConfiguration


class Command(NoArgsCommand):
    help = 'Create default SiteConfiguration for the default SITE_ID.'

    def handle_noargs(self, **options):
        s = Site.objects.get(id=settings.SITE_ID)

        try:
            if SiteConfiguration.objects.filter(site=s).exists():
                print("Default SiteConfiguration already exists. Doing nothing.")
            else:
                sc = SiteConfiguration(
                    site=s,
                    enabled=True)
                sc.save()
                print("Created default SiteConfiguration.")
        except Exception as e:
            print("Failed to create default configuration. Error: {0}".format(str(e)))
            sys.exit(-1)

