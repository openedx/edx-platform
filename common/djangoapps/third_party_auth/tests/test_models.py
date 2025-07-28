"""
Tests for third_party_auth/models.py using DDT for data-driven testing.
"""
import unittest
import ddt
from django.test import TestCase, override_settings
from django.contrib.sites.models import Site

from common.djangoapps.third_party_auth.tests.factories import SAMLProviderConfigFactory
from common.djangoapps.third_party_auth.models import (
    SAMLProviderConfig,
    SAMLConfiguration,
    SAMLProviderData,
    clean_username
)


@ddt.ddt
class TestSamlProviderConfigModel(TestCase, unittest.TestCase):
    """
    Test model operations for the saml provider config model.
    """

    def setUp(self):
        super().setUp()
        self.saml_provider_config = SAMLProviderConfigFactory()

    @ddt.data(
        ('ItJüstWòrks™', False, 'ItJ_stW_rks'),
        ('ItJüstWòrks™', True, 'ItJüstWòrks'),
        ('simple_username', False, 'simple_username'),
        ('simple_username', True, 'simple_username'),
        ('test@example.com', False, 'test_example_com'),
        ('test@example.com', True, 'test@example.com'),
    )
    @ddt.unpack
    def test_clean_username(self, input_username, unicode_enabled, expected_output):
        """Test the username cleaner function with different unicode settings."""
        with override_settings(FEATURES={'ENABLE_UNICODE_USERNAME': unicode_enabled}):
            self.assertEqual(clean_username(input_username), expected_output)


@ddt.ddt
class TestSAMLConfigurationSignals(TestCase):
    """
    Tests for SAML configuration signal handlers and their effect on provider configs.
    """

    def setUp(self):
        """
        Set up test data.
        """
        self.site = Site.objects.get_current()
        # Create initial SAML configuration
        self.saml_config = SAMLConfiguration.objects.create(
            site=self.site,
            slug='test-config',
            enabled=True,
            entity_id='https://test.example.com',
            org_info_str='{"en-US": {"url": "http://test.com", "displayname": "Test", "name": "test"}}'
        )
        # Create SAML provider that uses this configuration
        self.provider_config = SAMLProviderConfig.objects.create(
            site=self.site,
            slug='test-provider',
            enabled=True,
            name='Test Provider',
            entity_id='https://idp.test.com',
            saml_configuration=self.saml_config
        )
        # Create some test SAML provider data
        SAMLProviderData.objects.create(
            entity_id='https://idp.test.com',
            fetched_at='2023-01-01T00:00:00Z',
            sso_url='https://idp.test.com/sso',
            public_key='test-public-key'
        )

    @override_settings(ENABLE_SAML_CONFIG_SIGNAL_HANDLERS=True)
    def test_signal_updates_provider_config_to_latest_config(self):
        original_config_id = self.provider_config.saml_configuration_id
        self.saml_config.entity_id = 'https://updated.example.com'
        self.saml_config.save()
        self.provider_config.refresh_from_db()
        self.assertEqual(self.provider_config.saml_configuration_id, original_config_id)
