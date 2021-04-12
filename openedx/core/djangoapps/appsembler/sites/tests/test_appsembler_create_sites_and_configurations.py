"""
Test cases for create_sites_and_configurations command.

This test module is copied and modified to test supporting Appsembler
customizations

It is copied from `test_create_sites_and_configurations.py` in
`./openedx/core/djangoapps/theming/management/commands/tests/`
"""


import mock
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.management import CommandError, call_command
from django.test import TestCase

from oauth2_provider.models import Application
from openedx.core.djangoapps.oauth_dispatch.models import ApplicationAccess
from openedx.core.djangoapps.theming.models import SiteTheme
from student.models import UserProfile

from openedx.core.djangoapps.appsembler.auth.models import TrustedApplication


SITES = ["site_a", "site_b"]
MANAGEMENT_COMMAND_PATH = ('openedx.core.djangoapps.appsembler.sites.management'
                           '.commands.appsembler_create_sites_and_configurations.')


def _generate_site_config(dns_name, site_domain, devstack=False):
    """ Generate the site configuration for a given site """
    if devstack:
        lms_url_fmt = "{domain}-{dns_name}.e2e.devstack"
    else:
        lms_url_fmt = "{domain}-{dns_name}.sandbox.edx.org"

    return {
        "lms_url": lms_url_fmt.format(domain=site_domain, dns_name=dns_name),
        "platform_name": "{domain}-{dns_name}".format(domain=site_domain,
                                                      dns_name=dns_name)
    }


def _get_sites(dns_name, devstack=False):
    """ Creates the mocked data for management command """
    sites = {}

    if devstack:
        site_domain_fmt = "{site}-{dns_name}.e2e.devstack"
    else:
        site_domain_fmt = "{site}-{dns_name}.sandbox.edx.org"

    for site in SITES:
        sites.update({
            site: {
                "theme_dir_name": "{}_dir_name".format(site),
                "configuration": _generate_site_config(dns_name, site),
                "site_domain": site_domain_fmt.format(site=site, dns_name=dns_name)
            }
        })
    return sites


class TestCreateSiteAndConfiguration(TestCase):
    """ Test the create_site_and_configuration command """
    def setUp(self):
        super(TestCreateSiteAndConfiguration, self).setUp()

        self.dns_name = "dummy_dns"
        self.theme_path = "/dummyA/dummyB/"
        self.service_names = ['discovery', 'ecommerce']
        self.expected_app_names = [
            '{service_name}-sso-{site_name}'.format(
                site_name=site_name,
                service_name=service_name)
            for service_name in self.service_names
            for site_name in SITES
        ]
        self.command_under_test = 'appsembler_create_sites_and_configurations'

    def _assert_sites_are_valid(self):
        """
        Checks that data of all sites is valid
        """
        sites = Site.objects.filter(domain__contains=self.dns_name)
        self.assertEqual(len(sites), len(SITES))
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

        user_profile = UserProfile.objects.filter(user=service_user[0])
        self.assertEqual(len(user_profile), 1)
        return service_user

    def _assert_ecommerce_clients_are_valid(self, devstack=False):
        """
        Checks that all ecommerce clients are valid
        """
        service_user = self._assert_service_user_is_valid("ecommerce_worker")

        clients = Application.objects.filter(user=service_user[0])

        self.assertEqual(len(clients), len(SITES))

        if devstack:
            ecommerce_url_fmt = u"http://ecommerce-{site_name}-{dns_name}.e2e.devstack:18130/"
        else:
            ecommerce_url_fmt = u"https://ecommerce-{site_name}-{dns_name}.sandbox.edx.org/"

        for client in clients:
            self.assertEqual(client.user.username, service_user[0].username)
            site_name = [name for name in SITES if name in client.name][0]
            ecommerce_url = ecommerce_url_fmt.format(
                site_name=site_name,
                dns_name=self.dns_name
            )
            self.assertEqual(
                client.redirect_uris,
                "{ecommerce_url}complete/edx-oauth2/".format(ecommerce_url=ecommerce_url)
            )
            self.assertEqual(
                client.client_id,
                "ecommerce-key-{site_name}".format(site_name=site_name)
            )
            access = ApplicationAccess.objects.filter(application_id=client.id).first()
            self.assertEqual(
                access.scopes,
                ["user_id"]
            )

    def _assert_discovery_clients_are_valid(self, devstack=False):
        """
        Checks that all discovery clients are valid
        """
        service_user = self._assert_service_user_is_valid("lms_catalog_service_user")

        clients = Application.objects.filter(user=service_user[0])

        self.assertEqual(len(clients), len(SITES))

        if devstack:
            discovery_url_fmt = u"http://discovery-{site_name}-{dns_name}.e2e.devstack:18381/"
        else:
            discovery_url_fmt = u"https://discovery-{site_name}-{dns_name}.sandbox.edx.org/"

        for client in clients:
            self.assertEqual(client.user.username, service_user[0].username)
            site_name = [name for name in SITES if name in client.name][0]
            discovery_url = discovery_url_fmt.format(
                site_name=site_name,
                dns_name=self.dns_name
            )

            self.assertEqual(
                client.redirect_uris,
                "{discovery_url}complete/edx-oauth2/".format(discovery_url=discovery_url)
            )
            self.assertEqual(
                client.client_id,
                "discovery-key-{site_name}".format(site_name=site_name)
            )
            access = ApplicationAccess.objects.filter(application_id=client.id).first()
            self.assertEqual(
                access.scopes,
                ["user_id"]
            )

    def _assert_trusted_apps_are_valid(self):
        trusted_app_names = TrustedApplication.objects.values_list(
            'application__name', flat=True)
        assert set(trusted_app_names) == set(self.expected_app_names)

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
        assert TrustedApplication.objects.count() == 0
        mock_get_sites.return_value = _get_sites(self.dns_name)
        mock_commerce.return_value = None
        call_command(
            self.command_under_test,
            "--dns-name", self.dns_name,
            "--theme-path", self.theme_path
        )
        self._assert_sites_are_valid()
        self._assert_discovery_clients_are_valid()
        self._assert_ecommerce_clients_are_valid()
        self._assert_trusted_apps_are_valid()
        call_command(
            self.command_under_test,
            "--dns-name", self.dns_name,
            "--theme-path", self.theme_path
        )
        # if we run command with same dns then it will not duplicates the sites and oauth2 clients.
        self._assert_sites_are_valid()
        self._assert_discovery_clients_are_valid()
        self._assert_ecommerce_clients_are_valid()
        self._assert_trusted_apps_are_valid()
        self.dns_name = "new-dns"
        mock_get_sites.return_value = _get_sites(self.dns_name)
        call_command(
            self.command_under_test,
            "--dns-name", self.dns_name,
            "--theme-path", self.theme_path
        )
        # if we run command with different dns existing oauth2 clients are updated with new dns
        self._assert_sites_are_valid()
        self._assert_discovery_clients_are_valid()
        self._assert_ecommerce_clients_are_valid()
        self._assert_trusted_apps_are_valid()

    @mock.patch(MANAGEMENT_COMMAND_PATH + "Command._enable_commerce_configuration")
    @mock.patch(MANAGEMENT_COMMAND_PATH + "Command._get_sites_data")
    def test_with_devstack_and_dns(self, mock_get_sites, mock_commerce):
        """ Test the command with dns_name """
        mock_get_sites.return_value = _get_sites(self.dns_name, devstack=True)
        mock_commerce.return_value = None
        assert TrustedApplication.objects.count() == 0
        call_command(
            self.command_under_test,
            "--dns-name", self.dns_name,
            "--theme-path", self.theme_path,
            "--devstack"
        )
        self._assert_sites_are_valid()
        self._assert_discovery_clients_are_valid(devstack=True)
        self._assert_ecommerce_clients_are_valid(devstack=True)
        self._assert_trusted_apps_are_valid()
        call_command(
            self.command_under_test,
            "--dns-name", self.dns_name,
            "--theme-path", self.theme_path,
            "--devstack"
        )
        # if we run command with same dns then it will not duplicates the sites and oauth2 clients.
        self._assert_sites_are_valid()
        self._assert_discovery_clients_are_valid(devstack=True)
        self._assert_ecommerce_clients_are_valid(devstack=True)
        self._assert_trusted_apps_are_valid()
