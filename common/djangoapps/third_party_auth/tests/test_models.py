"""
Tests for third_party_auth/models.py.
"""
import unittest

from django.test import TestCase, override_settings
from django.contrib.sites.models import Site

from .factories import SAMLProviderConfigFactory
from ..models import (
    SAMLProviderConfig,
    SAMLConfiguration,
    SAMLProviderData,
    AuthNotConfigured,
    clean_username
)

# Import signal handlers to ensure they're loaded for tests
from ..signals import handlers  # noqa: F401 pylint: disable=unused-import


class TestSamlProviderConfigModel(TestCase, unittest.TestCase):
    """
    Test model operations for the saml provider config model.
    """

    def setUp(self):
        super().setUp()
        self.saml_provider_config = SAMLProviderConfigFactory()

    def test_unique_entity_id_enforcement_for_non_current_configs(self):
        """
        Test that the unique entity ID enforcement does not apply to noncurrent configs
        """
        with self.assertLogs() as ctx:
            assert len(SAMLProviderConfig.objects.all()) == 1
            old_entity_id = self.saml_provider_config.entity_id
            self.saml_provider_config.entity_id = f'{self.saml_provider_config.entity_id}-ayylmao'
            self.saml_provider_config.save()

            # check that we now have two records, one non-current
            assert len(SAMLProviderConfig.objects.all()) == 2
            assert len(SAMLProviderConfig.objects.current_set()) == 1

            # Make sure we can use that old entity id
            SAMLProviderConfigFactory(entity_id=old_entity_id)

            # 7/21/22 : Disabling the exception on duplicate entity ID's because of existing data.
            # with pytest.raises(IntegrityError):
            bad_config = SAMLProviderConfig(entity_id=self.saml_provider_config.entity_id)
            bad_config.save()
        assert ctx.records[0].msg == f'Entity ID: {self.saml_provider_config.entity_id} already in use'

    @override_settings(FEATURES={'ENABLE_UNICODE_USERNAME': False})
    def test_clean_username_unicode_disabled(self):
        """
        Test the username cleaner function with unicode disabled
        """
        assert clean_username('ItJüstWòrks™') == 'ItJ_stW_rks'

    @override_settings(FEATURES={'ENABLE_UNICODE_USERNAME': True})
    def test_clean_username_unicode_enabled(self):
        """
        Test the username cleaner function with unicode enabled
        """
        assert clean_username('ItJüstWòrks™') == 'ItJüstWòrks'


class TestSAMLConfigurationSignals(TestCase):
    """Test the simplified SAML configuration management approach."""

    def setUp(self):
        """Set up test data."""
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

    def test_get_current_saml_configuration_returns_assigned_config(self):
        """Test that get_current_saml_configuration returns the assigned configuration."""
        current_config = self.provider_config.get_current_saml_configuration()
        self.assertEqual(current_config.id, self.saml_config.id)
        self.assertEqual(current_config.entity_id, 'https://test.example.com')

    def test_get_current_saml_configuration_fallback_to_default(self):
        """Test that method falls back to default configuration when none is set."""
        # Create default configuration
        default_config = SAMLConfiguration.objects.create(
            site=self.site,
            slug='default',
            enabled=True,
            entity_id='https://default.example.com',
            org_info_str='{"en-US": {"url": "http://default.com", "displayname": "Default", "name": "default"}}'
        )

        # Create provider without SAML configuration
        provider_without_config = SAMLProviderConfig.objects.create(
            site=self.site,
            slug='provider-without-config',
            enabled=True,
            name='Provider Without Config',
            entity_id='https://idp.noconfig.com',
            saml_configuration=None
        )

        # Should fall back to default
        current_config = provider_without_config.get_current_saml_configuration()
        self.assertEqual(current_config.slug, 'default')
        self.assertEqual(current_config.id, default_config.id)

    def test_get_config_works_with_valid_configuration(self):
        """Test that get_config works when valid configuration is present."""
        # Should work without raising AuthNotConfigured
        config = self.provider_config.get_config()
        self.assertIsNotNone(config)
        self.assertEqual(config.conf['saml_sp_configuration'].entity_id, 'https://test.example.com')

    def test_get_config_raises_auth_not_configured_when_no_saml_config(self):
        """Test that get_config raises AuthNotConfigured when no SAML configuration is available."""
        # Create provider without SAML configuration and no default
        provider_without_config = SAMLProviderConfig.objects.create(
            site=self.site,
            slug='provider-without-config',
            enabled=True,
            name='Provider Without Config',
            entity_id='https://idp.noconfig.com',
            saml_configuration=None
        )

        # Delete ALL existing SAML configurations to ensure the test scenario
        SAMLConfiguration.objects.all().delete()

        # Should raise AuthNotConfigured due to missing SAML configuration
        with self.assertRaises(AuthNotConfigured):
            provider_without_config.get_config()

    def test_signal_prevents_duplicate_provider_configs(self):
        """Test that signal handler updates existing records instead of creating duplicates."""
        # Get initial count of SAMLProviderConfig records
        initial_provider_count = SAMLProviderConfig.objects.count()

        # Store original provider config ID
        original_provider_id = self.provider_config.id
        original_saml_config_id = self.provider_config.saml_configuration_id

        # Update the SAML configuration to trigger signal
        self.saml_config.entity_id = 'https://updated.example.com'
        self.saml_config.save()  # This creates a new SAMLConfiguration record

        # Verify that NO new SAMLProviderConfig was created
        final_provider_count = SAMLProviderConfig.objects.count()
        self.assertEqual(
            initial_provider_count,
            final_provider_count,
            "Signal handler should NOT create new SAMLProviderConfig records"
        )

        # Verify the existing provider was updated (not replaced)
        self.provider_config.refresh_from_db()
        self.assertEqual(
            self.provider_config.id,
            original_provider_id,
            "Provider config ID should remain the same (no new record created)"
        )

        # Verify the provider now points to the new configuration
        self.assertNotEqual(
            self.provider_config.saml_configuration_id,
            original_saml_config_id,
            "Provider should point to new SAMLConfiguration ID"
        )
        self.assertEqual(
            self.provider_config.saml_configuration_id,
            self.saml_config.id,
            "Provider should point to the updated SAMLConfiguration"
        )


class TestSAMLConfigurationManagementCommand(TestCase):
    """Test the SAML management command's fix-references functionality."""

    def setUp(self):
        """Set up test data."""
        self.site = Site.objects.get_current()

        # Create SAML configuration
        self.saml_config = SAMLConfiguration.objects.create(
            site=self.site,
            slug='test-config',
            enabled=True,
            entity_id='https://test.example.com',
            org_info_str='{"en-US": {"url": "http://test.com", "displayname": "Test", "name": "test"}}'
        )

        # Create provider config
        self.provider_config = SAMLProviderConfig.objects.create(
            site=self.site,
            slug='test-provider',
            enabled=True,
            name='Test Provider',
            entity_id='https://idp.test.com',
            saml_configuration=self.saml_config
        )

    def test_command_identifies_outdated_references(self):
        """Test that the command correctly identifies outdated references."""
        from django.core.management import call_command
        from io import StringIO

        # Update SAML config to create new version
        self.saml_config.entity_id = 'https://updated.example.com'
        self.saml_config.save()

        # Manually set provider to old version
        old_configs = SAMLConfiguration.objects.filter(
            site=self.site,
            slug='test-config',
            enabled=False
        ).order_by('-change_date')

        if old_configs.exists():
            old_config = old_configs.first()
            self.provider_config.saml_configuration = old_config
            self.provider_config.save()

            # Run command in dry-run mode
            out = StringIO()
            call_command('saml', '--fix-references', '--dry-run', stdout=out)
            output = out.getvalue()

            # Should identify the outdated reference
            self.assertIn('test-provider', output)
            self.assertIn('outdated config', output)

    def test_command_fixes_outdated_references(self):
        """Test that the command actually fixes outdated references."""
        from django.core.management import call_command
        from io import StringIO

        # Update SAML config to create new version
        self.saml_config.entity_id = 'https://updated.example.com'
        self.saml_config.save()
        new_config_id = self.saml_config.id

        # Manually set provider to old version
        old_configs = SAMLConfiguration.objects.filter(
            site=self.site,
            slug='test-config',
            enabled=False
        ).order_by('-change_date')

        if old_configs.exists():
            old_config = old_configs.first()
            self.provider_config.saml_configuration = old_config
            self.provider_config.save()

            # Run command to fix references
            out = StringIO()
            call_command('saml', '--fix-references', stdout=out)

            # Verify provider now points to new config
            self.provider_config.refresh_from_db()
            self.assertEqual(self.provider_config.saml_configuration_id, new_config_id)
