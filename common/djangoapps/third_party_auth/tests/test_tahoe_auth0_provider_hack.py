"""
Tests for the hacks we have to enable the tahoe-auth0 package.
"""

import unittest
from unittest.mock import patch

import ddt
from django.contrib.sites.models import Site

from openedx.core.djangoapps.site_configuration.tests.test_util import with_site_configuration_context
from third_party_auth.tests import testutil

SITE_DOMAIN_A = 'professionalx.example.com'
SITE_DOMAIN_B = 'somethingelse.example.com'


@unittest.skipUnless(testutil.AUTH_FEATURE_ENABLED, testutil.AUTH_FEATURES_KEY + ' not enabled')
@ddt.ddt
class TahoeAuth0IntegrationHackTests(testutil.TestCase):
    """Tests registry discovery and operation."""

    def test_is_auth0_disabled_for_no_tahoe_auth0(self):
        prov = self.configure_oauth_provider(enabled=True, backend_name="dummy")

        with with_site_configuration_context(configuration={"ENABLE_TAHOE_AUTH0": True}):
            with self.settings(FEATURES={"ENABLE_TAHOE_AUTH0": True}):
                self.assertEqual(prov.enabled_for_current_site, False)

    def test_is_auth0_enabled_for_site_configuration(self):
        """
        Verify that Tahoe Auth0 is enabled when the Site Configuration asks for it.
        """
        prov = self.configure_oauth_provider(enabled=True, backend_name="tahoe-auth0")

        with with_site_configuration_context(configuration={"ENABLE_TAHOE_AUTH0": True}):
            with self.settings(FEATURES={"ENABLE_TAHOE_AUTH0": True}):
                self.assertEqual(prov.enabled_for_current_site, True)

            with self.settings(FEATURES={"ENABLE_TAHOE_AUTH0": False}):
                self.assertEqual(prov.enabled_for_current_site, True)

    def test_is_auth0_publicly_configured(self):
        """
        Verify that Tahoe Auth0 is enabled or disabled based on the public setting
        if the Site Configuration doesn't specify a custom value.
        """
        prov = self.configure_oauth_provider(enabled=True, backend_name="tahoe-auth0")

        with with_site_configuration_context(configuration={}):
            with self.settings(FEATURES={"ENABLE_TAHOE_AUTH0": True}):
                self.assertEqual(prov.enabled_for_current_site, True)

            with self.settings(FEATURES={"ENABLE_TAHOE_AUTH0": False}):
                self.assertEqual(prov.enabled_for_current_site, False)

    @patch.dict('django.conf.settings.FEATURES', {'ENABLE_TAHOE_AUTH0': True})
    @ddt.data(
        {'auth0_backend_enabled': False, 'domain_name': SITE_DOMAIN_A},
        {'auth0_backend_enabled': False, 'domain_name': SITE_DOMAIN_B},
        {'auth0_backend_enabled': True, 'domain_name': SITE_DOMAIN_A},
        {'auth0_backend_enabled': True, 'domain_name': SITE_DOMAIN_B},
    )
    @ddt.unpack
    def test_auth0_feature_enabled_with_different_sites(self, auth0_backend_enabled, domain_name):
        """
        Verify that enabled_for_current_site returns True when Auth0 provider is configured
        for a different site.

        The `ProviderConfig.enabled` (auth0_backend_enabled) property is disregarded.
        """
        site_b, _created = Site.objects.get_or_create(domain=SITE_DOMAIN_B, name=SITE_DOMAIN_B)
        with with_site_configuration_context(domain_name):
            prov = self.configure_oauth_provider(enabled=auth0_backend_enabled, site=site_b, backend_name="tahoe-auth0")
            assert prov.enabled_for_current_site, 'Backend should be shown when ENABLE_TAHOE_AUTH0 is enabled'

    @patch.dict('django.conf.settings.FEATURES', {'ENABLE_TAHOE_AUTH0': False})
    @ddt.data(
        {'auth0_backend_enabled': False, 'domain_name': SITE_DOMAIN_A},
        {'auth0_backend_enabled': False, 'domain_name': SITE_DOMAIN_B},
        {'auth0_backend_enabled': True, 'domain_name': SITE_DOMAIN_A},
        {'auth0_backend_enabled': True, 'domain_name': SITE_DOMAIN_B},
    )
    @ddt.unpack
    def test_auth0_feature_disabled_with_different_sites(self, auth0_backend_enabled, domain_name):
        """
        Verify that enabled_for_current_site returns False when ENABLE_TAHOE_AUTH0 is set to False.

        The `ProviderConfig.enabled` (auth0_backend_enabled) property is disregarded.
        """
        site_b, _created = Site.objects.get_or_create(domain=SITE_DOMAIN_B, name=SITE_DOMAIN_B)
        with with_site_configuration_context(domain_name):
            prov = self.configure_oauth_provider(enabled=auth0_backend_enabled, site=site_b, backend_name="tahoe-auth0")
            assert not prov.enabled_for_current_site, 'Backend should be hidden when ENABLE_TAHOE_AUTH0 is disabled'
