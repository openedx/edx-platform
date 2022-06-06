"""
Tests for the hacks we have to enable the tahoe-idp package with the Third Party Auth in Open edX.
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
class TahoeIdpIntegrationHackTests(testutil.TestCase):
    """Tests TPA registry discovery and operation with tahoe-idp."""

    def test_is_idp_disabled_for_no_tahoe_idp(self):
        prov = self.configure_oauth_provider(enabled=True, backend_name="dummy")

        with with_site_configuration_context(configuration={"ENABLE_TAHOE_IDP": True}):
            with self.settings(FEATURES={"ENABLE_TAHOE_IDP": True}):
                self.assertEqual(prov.enabled_for_current_site, False)

    def test_is_idp_enabled_for_site_configuration(self):
        """
        Verify that Tahoe Idp is enabled when the Site Configuration asks for it.
        """
        prov = self.configure_oauth_provider(enabled=True, backend_name="tahoe-idp")

        with with_site_configuration_context(configuration={"ENABLE_TAHOE_IDP": True}):
            with self.settings(FEATURES={"ENABLE_TAHOE_IDP": True}):
                self.assertEqual(prov.enabled_for_current_site, True)

            with self.settings(FEATURES={"ENABLE_TAHOE_IDP": False}):
                self.assertEqual(prov.enabled_for_current_site, True)

    def test_is_idp_publicly_configured(self):
        """
        Verify that Tahoe Idp is enabled or disabled based on the public setting
        if the Site Configuration doesn't specify a custom value.
        """
        prov = self.configure_oauth_provider(enabled=True, backend_name="tahoe-idp")

        with with_site_configuration_context(configuration={}):
            with self.settings(FEATURES={"ENABLE_TAHOE_IDP": True}):
                self.assertEqual(prov.enabled_for_current_site, True)

            with self.settings(FEATURES={"ENABLE_TAHOE_IDP": False}):
                self.assertEqual(prov.enabled_for_current_site, False)

    @patch.dict('django.conf.settings.FEATURES', {'ENABLE_TAHOE_IDP': True})
    @ddt.data(
        {'idp_backend_enabled': False, 'domain_name': SITE_DOMAIN_A},
        {'idp_backend_enabled': False, 'domain_name': SITE_DOMAIN_B},
        {'idp_backend_enabled': True, 'domain_name': SITE_DOMAIN_A},
        {'idp_backend_enabled': True, 'domain_name': SITE_DOMAIN_B},
    )
    @ddt.unpack
    def test_idp_feature_enabled_with_different_sites(self, idp_backend_enabled, domain_name):
        """
        Verify that enabled_for_current_site returns True when Idp provider is configured
        for a different site.

        The `ProviderConfig.enabled` (idp_backend_enabled) property is disregarded.
        """
        site_b, _created = Site.objects.get_or_create(domain=SITE_DOMAIN_B, name=SITE_DOMAIN_B)
        with with_site_configuration_context(domain_name):
            prov = self.configure_oauth_provider(enabled=idp_backend_enabled, site=site_b, backend_name="tahoe-idp")
            assert prov.enabled_for_current_site, 'Backend should be shown when ENABLE_TAHOE_IDP is enabled'

    @patch.dict('django.conf.settings.FEATURES', {'ENABLE_TAHOE_IDP': False})
    @ddt.data(
        {'idp_backend_enabled': False, 'domain_name': SITE_DOMAIN_A},
        {'idp_backend_enabled': False, 'domain_name': SITE_DOMAIN_B},
        {'idp_backend_enabled': True, 'domain_name': SITE_DOMAIN_A},
        {'idp_backend_enabled': True, 'domain_name': SITE_DOMAIN_B},
    )
    @ddt.unpack
    def test_idp_feature_disabled_with_different_sites(self, idp_backend_enabled, domain_name):
        """
        Verify that enabled_for_current_site returns False when ENABLE_TAHOE_IDP is set to False.

        The `ProviderConfig.enabled` (idp_backend_enabled) property is disregarded.
        """
        site_b, _created = Site.objects.get_or_create(domain=SITE_DOMAIN_B, name=SITE_DOMAIN_B)
        with with_site_configuration_context(domain_name):
            prov = self.configure_oauth_provider(enabled=idp_backend_enabled, site=site_b, backend_name="tahoe-idp")
            assert not prov.enabled_for_current_site, 'Backend should be hidden when ENABLE_TAHOE_IDP is disabled'
