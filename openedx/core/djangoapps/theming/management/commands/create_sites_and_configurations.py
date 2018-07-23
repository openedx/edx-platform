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
    ecommerce_base_url_fmt = None
    ecommerce_oidc_url = None
    discovery_user = None
    discovery_base_url_fmt = None
    discovery_oidc_url = None
    journals = False
    journals_user = None
    journals_base_url_fmt = None
    journals_oidc_url = None

    configuration_filename = None

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

        parser.add_argument(
            "--devstack",
            action='store_true',
            help="Use devstack config, otherwise sandbox config is assumed",
        )

        parser.add_argument(
            "--enable-journals",
            dest="journals",
            action="store_true",
            help="Enable journal configuration",
        )

    def _create_oauth2_client(self, url, site_name, service_name, service_user):
        """
        Creates the oauth2 client and add it in trusted clients.
        """
        client_id = "{service_name}-key{site_name}".format(
            service_name=service_name,
            site_name="" if site_name == "edx" else "-{}".format(site_name)
        )
        client, created = Client.objects.update_or_create(
            client_id=client_id,
            defaults={
                "user": service_user,
                "name": "{site_name}_{service_name}_client".format(
                    site_name=site_name,
                    service_name=service_name,
                ),
                "url": url,
                "client_secret": "{service_name}-secret".format(
                    service_name=service_name
                ),
                "client_type": CONFIDENTIAL,
                "redirect_uri": "{url}complete/edx-oidc/".format(url=url),
                "logout_uri": "{url}logout/".format(url=url)
            }
        )
        if created:
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

    def _update_default_clients(self):
        """
        These two clients are being created by default without service
        users so we have to associate the service users to them.
        """
        ecommerce_queryset = Client.objects.filter(redirect_uri=self.ecommerce_oidc_url)

        if ecommerce_queryset:
            ecommerce_client = ecommerce_queryset[0]
            ecommerce_client.user = self.ecommerce_user
            ecommerce_client.save()

        discovery_queryset = Client.objects.filter(redirect_uri=self.discovery_oidc_url)
        if discovery_queryset:
            discovery_client = discovery_queryset[0]
            discovery_client.user = self.discovery_user
            discovery_client.save()

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
        for config_file in self.find(self.configuration_filename, self.theme_path):
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
        Creates the service user for ecommerce, discovery and journals.
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
        self.dns_name = options['dns_name']
        self.theme_path = options['theme_path']
        self.journals = options['journals']

        if options['devstack']:
            configuration_prefix = "devstack"
            self.discovery_oidc_url = "http://discovery-{}.e2e.devstack:18381/complete/edx-oidc/".format(self.dns_name)
            self.discovery_base_url_fmt = "http://discovery-{site_domain}:18381/"
            self.ecommerce_oidc_url = "http://ecommerce-{}.e2e.devstack:18130/complete/edx-oidc/".format(self.dns_name)
            self.ecommerce_base_url_fmt = "http://ecommerce-{site_domain}:18130/"
            self.journals_oidc_url = "http://journals-{}.e2e.devstack:18606/complete/edx-oidc/".format(self.dns_name)
            self.journals_base_url_fmt = "http://journals-{site_domain}:18606/"
        else:
            configuration_prefix = "sandbox"
            self.discovery_oidc_url = "https://discovery-{}.sandbox.edx.org/complete/edx-oidc/".format(self.dns_name)
            self.discovery_base_url_fmt = "https://discovery-{site_domain}/"
            self.ecommerce_oidc_url = "https://ecommerce-{}.sandbox.edx.org/complete/edx-oidc/".format(self.dns_name)
            self.ecommerce_base_url_fmt = "https://ecommerce-{site_domain}/"
            self.journals_oidc_url = "https://journals-{}.sandbox.edx.org/complete/edx-oidc/".format(self.dns_name)
            self.journals_base_url_fmt = "https://journals-{site_domain}/"

        self.configuration_filename = '{}_configuration.json'.format(configuration_prefix)
        self.discovery_user = self.get_or_create_service_user("lms_catalog_service_user")
        self.ecommerce_user = self.get_or_create_service_user("ecommerce_worker")
        if self.journals:
            self.journals_user = self.get_or_create_service_user("journals_worker")

        all_sites = self._get_sites_data()
        self._update_default_clients()

        # creating Sites, SiteThemes, SiteConfigurations and oauth2 clients
        for site_name, site_data in all_sites.items():
            site_domain = site_data['site_domain']

            discovery_url = self.discovery_base_url_fmt.format(site_domain=site_domain)
            ecommerce_url = self.ecommerce_base_url_fmt.format(site_domain=site_domain)
            journals_url = self.journals_base_url_fmt.format(site_domain=site_domain)

            LOG.info("Creating '{site_name}' Site".format(site_name=site_name))
            self._create_sites(site_domain, site_data['theme_dir_name'], site_data['configuration'])

            LOG.info("Creating discovery oauth2 client for '{site_name}' site".format(site_name=site_name))
            self._create_oauth2_client(discovery_url, site_name, 'discovery', self.discovery_user)

            LOG.info("Creating ecommerce oauth2 client for '{site_name}' site".format(site_name=site_name))
            self._create_oauth2_client(ecommerce_url, site_name, 'ecommerce', self.ecommerce_user)

            if self.journals:
                LOG.info("Creating journals oauth2 client for '{site_name}' site".format(site_name=site_name))
                self._create_oauth2_client(journals_url, site_name, 'journals', self.journals_user)

        self._enable_commerce_configuration()
