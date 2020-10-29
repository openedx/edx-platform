"""
Run by ansible to setup a single site configuration in sandbox environments
"""
import json
import logging
from textwrap import dedent

from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand

from openedx.core.djangoapps.site_configuration.models import SiteConfiguration

LOG = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Command to create a configuration for a single site.  If the site does not
    already exist one will be created.

    Example:
    ./manage.py lms create_configuration uox.sandbox.edx.org
      --configuration="{'COURSE_CATALOG_API_URL':'https://discovery-uox.sandbox.edx.org/api/v1'}"
    """
    help = dedent(__doc__).strip()

    def add_arguments(self, parser):
        parser.add_argument('domain')
        parser.add_argument(
            '--configuration',
            type=json.loads,
            help="Enter JSON site configuration",
            required=False,
            default=''
        )

    def handle(self, *args, **options):
        domain = options['domain']
        configuration = options['configuration']
        site, created = Site.objects.get_or_create(
            domain=domain,
            name=domain,
        )
        if created:
            LOG.info(u"Site does not exist. Created new site '{site_name}'".format(site_name=domain))
        else:
            LOG.info(u"Found existing site for '{site_name}'".format(site_name=domain))

        LOG.info(u"Creating '{site_name}' SiteConfiguration".format(site_name=domain))
        SiteConfiguration.objects.create(site=site, values=configuration, enabled=True)
