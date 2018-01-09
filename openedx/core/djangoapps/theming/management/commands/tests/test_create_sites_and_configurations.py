"""
Test cases for create_sites_and_configurations command.
"""

import mock

from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.management import call_command, CommandError

from provider.oauth2.models import Client
from edx_oauth2_provider.models import TrustedClient
from openedx.core.djangoapps.theming.models import SiteTheme
from student.models import UserProfile

SITES = ["site_a", "site_b"]
MANAGEMENT_COMMAND_PATH = "openedx.core.djangoapps.theming.management.commands.create_sites_and_configurations."


def _generate_site_config(dns_name, site_domain):
    """ Generate the site configuration for a given site """
    return {
        "lms_url": "{domain}-{dns_name}.sandbox.edx.org".format(domain=site_domain, dns_name=dns_name),
        "platform_name": "{domain}-{dns_name}".format(domain=site_domain, dns_name=dns_name)
    }


def _get_sites(dns_name):
    """ Creates the mocked data for management command """
    sites = {}
    for site in SITES:
        sites.update({
            site: {
                "theme_dir_name": "{}_dir_name".format(site),
                "configuration": _generate_site_config(dns_name, site),
                "site_domain": "{site}-{dns_name}.sandbox.edx.org".format(site=site, dns_name=dns_name)
            }
        })
    return sites


class TestCreateSiteAndConfiguration(TestCase):
    """ Test the create_site_and_configuration command """
    def setUp(self):
        super(TestCreateSiteAndConfiguration, self).setUp()

        self.dns_name = "dummy_dns"
        self.theme_path = "/dummyA/dummyB/"

    def _assert_sites_are_valid(self):
        """
        Checks that data of all sites is valid
        """
        sites = Site.objects.all()
        # there is an extra default site.
        self.assertEqual(len(sites), len(SITES) + 1)
        for site in sites:
            if site.name in SITES:
                site_theme = SiteTheme.objects.get(site=site)

                self.assertEqual(
                    site_theme.theme_dir_name,
                    "{}_dir_name".format(site.name)
                )

                self.assertDictEqual(
                    dict(site.configuration.values),
                    _generate_site_config(self.dns_name, site.name)
                )

    def _assert_service_user_is_valid(self, username):
        service_user = User.objects.filter(username=username)
        self.assertEqual(len(service_user), 1)
        self.assertTrue(service_user[0].is_active)
        self.assertTrue(service_user[0].is_staff)
        self.assertTrue(service_user[0].is_superuser)

        user_profile = UserProfile.objects.filter(user=service_user)
        self.assertEqual(len(user_profile), 1)
        return service_user

    def _assert_ecommerce_clients_are_valid(self):
        """
        Checks that all ecommerce clients are valid
        """
        service_user = self._assert_service_user_is_valid("ecommerce_worker")

        clients = Client.objects.filter(user=service_user)
        self.assertEqual(len(clients), len(SITES))

        for client in clients:
            self.assertEqual(client.user.username, service_user[0].username)
            site_name = client.name[:6]
            ecommerce_url = "https://ecommerce-{site_name}-{dns_name}.sandbox.edx.org/".format(
                site_name=site_name,
                dns_name=self.dns_name
            )
            self.assertEqual(client.url, ecommerce_url)
            self.assertEqual(
                client.redirect_uri,
                "{ecommerce_url}complete/edx-oidc/".format(ecommerce_url=ecommerce_url)
            )
            self.assertEqual(
                len(TrustedClient.objects.filter(client=client)),
                1
            )

    def _assert_discovery_clients_are_valid(self):
        """
        Checks that all discovery clients are valid
        """
        service_user = self._assert_service_user_is_valid("lms_catalog_service_user")

        clients = Client.objects.filter(user=service_user)
        self.assertEqual(len(clients), len(SITES))

        for client in clients:
            self.assertEqual(client.user.username, service_user[0].username)
            site_name = client.name[:6]
            discovery_url = "https://discovery-{site_name}-{dns_name}.sandbox.edx.org/".format(
                site_name=site_name,
                dns_name=self.dns_name
            )
            self.assertEqual(client.url, discovery_url)
            self.assertEqual(
                client.redirect_uri,
                "{discovery_url}complete/edx-oidc/".format(discovery_url=discovery_url)
            )
            self.assertEqual(
                len(TrustedClient.objects.filter(client=client)),
                1
            )

    def test_without_dns(self):
        """ Test the command without dns_name """
        with self.assertRaises(CommandError):
            call_command(
                "create_sites_and_configurations"
            )

    @mock.patch(MANAGEMENT_COMMAND_PATH + "Command._enable_commerce_configuration")
    @mock.patch(MANAGEMENT_COMMAND_PATH + "Command._get_sites_data")
    def test_with_dns(self, mock_get_sites, mock_commerce):
        """ Test the command with dns_name """
        mock_get_sites.return_value = _get_sites(self.dns_name)
        mock_commerce.return_value = None
        call_command(
            "create_sites_and_configurations",
            "--dns-name", self.dns_name,
            "--theme-path", self.theme_path
        )
        self._assert_sites_are_valid()
        self._assert_discovery_clients_are_valid()
        self._assert_ecommerce_clients_are_valid()

        call_command(
            "create_sites_and_configurations",
            "--dns-name", self.dns_name,
            "--theme-path", self.theme_path
        )
        # if we run command with same dns then it will not duplicates the sites and oauth2 clients.
        self._assert_sites_are_valid()
        self._assert_discovery_clients_are_valid()
        self._assert_ecommerce_clients_are_valid()
