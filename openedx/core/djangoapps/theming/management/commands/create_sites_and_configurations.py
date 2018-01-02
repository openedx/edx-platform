"""
This command will be run by an ansible script.
"""

import os
import json
import fnmatch
import logging

from provider.oauth2.models import Client
from provider.constants import CONFIDENTIAL
from edx_oauth2_provider.models import TrustedClient
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand

from lms.djangoapps.commerce.models import CommerceConfiguration
from openedx.core.djangoapps.theming.models import SiteTheme
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from student.models import UserProfile

LOG = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Command to create the site, site themes, configuration and oauth2 clients for all WL-sites.

    Example:
    ./manage.py lms create_sites_and_configurations --dns-name whitelabel --theme-path /edx/src/edx-themes/edx-platform
    """
    dns_name = None
    theme_path = None
    ecommerce_user = None
    discovery_user = None

    def add_arguments(self, parser):
        """
        Add arguments to the command parser.
        """
        parser.add_argument(
            "--dns-name",
            type=str,
            help="Enter DNS name of sandbox.",
            required=True
        )

        parser.add_argument(
            "--theme-path",
            type=str,
            help="Enter theme directory path",
            required=True
        )

    def _create_oauth2_client(self, url, site_name, is_discovery=True):
        """
        Creates the oauth2 client and add it in trusted clients.
        """

        client, _ = Client.objects.get_or_create(
            redirect_uri="{url}complete/edx-oidc/".format(url=url),
            defaults={
                "user": self.discovery_user if is_discovery else self.ecommerce_user,
                "name": "{site_name}_{client_type}_client".format(
                    site_name=site_name,
                    client_type="discovery" if is_discovery else "ecommerce",
                ),
                "url": url,
                "client_id": "{client_type}-key-{site_name}".format(
                    client_type="discovery" if is_discovery else "ecommerce",
                    site_name=site_name
                ),
                "client_secret": "{client_type}-secret-{dns_name}".format(
                    client_type="discovery" if is_discovery else "ecommerce",
                    dns_name=self.dns_name
                ),
                "client_type": CONFIDENTIAL,
                "logout_uri": "{url}logout/".format(url=url)
            }
        )
        LOG.info("Adding {client} oauth2 client as trusted client".format(client=client.name))
        TrustedClient.objects.get_or_create(client=client)

    def _create_sites(self, site_domain, theme_dir_name, site_configuration):
        """
        Create Sites, SiteThemes and SiteConfigurations
        """
        site, created = Site.objects.get_or_create(
            domain=site_domain,
            defaults={"name": theme_dir_name}
        )
        if created:
            LOG.info("Creating '{site_name}' SiteTheme".format(site_name=site_domain))
            SiteTheme.objects.create(site=site, theme_dir_name=theme_dir_name)

            LOG.info("Creating '{site_name}' SiteConfiguration".format(site_name=site_domain))
            SiteConfiguration.objects.create(site=site, values=site_configuration, enabled=True)
        else:
            LOG.info("'{site_domain}' site already exists".format(site_domain=site_domain))

    def find(self, pattern, path):
        """
        Matched the given pattern in given path and returns the list of matching files
        """
        result = []
        for root, dirs, files in os.walk(path):  # pylint: disable=unused-variable
            for name in files:
                if fnmatch.fnmatch(name, pattern):
                    result.append(os.path.join(root, name))
        return result

    def _enable_commerce_configuration(self):
        """
        Enable the commerce configuration.
        """
        CommerceConfiguration.objects.get_or_create(
            enabled=True,
            checkout_on_ecommerce_service=True
        )

    def _get_sites_data(self):
        """
        Reads the json files from theme directory and returns the site data in JSON format.
        "site_a":{
            "theme_dir_name": "site_a.edu.au"
            "configuration": {
                "key1": "value1",
                "key2": "value2"
            }
        }
        """
        site_data = {}
        for config_file in self.find('sandbox_configuration.json', self.theme_path):
            LOG.info("Reading file from {file}".format(file=config_file))
            configuration_data = json.loads(
                json.dumps(
                    json.load(
                        open(config_file)
                    )
                ).replace("{dns_name}", self.dns_name)
            )['lms_configuration']

            site_data[configuration_data['sandbox_name']] = {
                "site_domain": configuration_data['site_domain'],
                "theme_dir_name": configuration_data['theme_dir_name'],
                "configuration": configuration_data['configuration']
            }
        return site_data

    def get_or_create_service_user(self, username):
        """
        Creates the service user for ecommerce and discovery.
        """
        service_user, _ = User.objects.get_or_create(username=username)
        service_user.is_active = True
        service_user.is_staff = True
        service_user.is_superuser = True
        service_user.save()

        # Without User profile we cannot publish the course from ecommerce to LMS.
        UserProfile.objects.get_or_create(
            user=service_user,
            defaults={
                "name": username
            }
        )
        return service_user

    def handle(self, *args, **options):

        self.theme_path = options['theme_path']
        self.dns_name = options['dns_name']

        self.discovery_user = self.get_or_create_service_user("lms_catalog_service_user")
        self.ecommerce_user = self.get_or_create_service_user("ecommerce_worker")

        all_sites = self._get_sites_data()

        # creating Sites, SiteThemes, SiteConfigurations and oauth2 clients
        for site_name, site_data in all_sites.items():
            site_domain = site_data['site_domain']

            discovery_url = "https://discovery-{site_domain}/".format(site_domain=site_domain)
            ecommerce_url = "https://ecommerce-{site_domain}/".format(site_domain=site_domain)

            LOG.info("Creating '{site_name}' Site".format(site_name=site_name))
            self._create_sites(site_domain, site_data['theme_dir_name'], site_data['configuration'])

            LOG.info("Creating discovery oauth2 client for '{site_name}' site".format(site_name=site_name))
            self._create_oauth2_client(discovery_url, site_name, is_discovery=True)

            LOG.info("Creating ecommerce oauth2 client for '{site_name}' site".format(site_name=site_name))
            self._create_oauth2_client(ecommerce_url, site_name, is_discovery=False)

        self._enable_commerce_configuration()
