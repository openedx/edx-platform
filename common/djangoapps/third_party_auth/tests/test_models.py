"""
Tests for third_party_auth/models.py using DDT for data-driven testing.
"""
import unittest
from unittest.mock import patch, call

import ddt
from django.test import TestCase, override_settings, TransactionTestCase
from django.contrib.sites.models import Site
from django.db import transaction

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


@ddt.ddt
class TestSamlProviderConfigModel(TestCase, unittest.TestCase):
    """Test model operations for the saml provider config model."""

    def setUp(self):
        super().setUp()
        self.saml_provider_config = SAMLProviderConfigFactory()

    def test_unique_entity_id_enforcement_for_non_current_configs(self):
        """Test that the unique entity ID enforcement does not apply to noncurrent configs"""
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
    """Test the simplified SAML configuration management approach using DDT."""

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

    @override_settings(ENABLE_SAML_CONFIG_SIGNAL_HANDLERS=True)
    @patch('common.djangoapps.third_party_auth.signals.handlers.set_custom_attribute')
    def test_signal_custom_attributes(self, mock_set_custom_attribute):
        """Test that signal handler sets custom attributes during updates."""
        # Update SAML configuration to trigger signal
        self.saml_config.entity_id = 'https://updated.example.com'
        self.saml_config.save()

        # Verify both custom attributes were set
        expected_calls = [
            call('saml_config.signal_update', 'updated_reference'),
            call('saml_config.signal_behavior', 'active')
        ]
        mock_set_custom_attribute.assert_has_calls(expected_calls, any_order=True)

    @ddt.data(
        ('direct', 'saml_config.using', 'direct'),
        ('default', 'saml_config.using', 'default'),
        ('none_found', 'saml_config.using', 'none_found'),
    )
    @ddt.unpack
    @override_settings(ENABLE_SAML_CONFIG_SIGNAL_HANDLERS=True)
    @patch('common.djangoapps.third_party_auth.models.set_custom_attribute')
    @patch('common.djangoapps.third_party_auth.models.SAMLConfiguration.current')
    def test_custom_attributes_tracking_scenarios(self, scenario, expected_attr_name, expected_attr_value, mock_saml_current, mock_set_custom_attribute):
        """Test that custom attributes track SAML configuration usage scenarios."""
        if scenario == 'direct':
            # Test direct configuration - mock not needed, use real config
            mock_saml_current.return_value = None  # Don't interfere with direct config
            config = self.provider_config.get_current_saml_configuration()
            self.assertIsNotNone(config)

        elif scenario == 'default':
            # Test default fallback
            self.provider_config.saml_configuration = None
            self.provider_config.save()

            # Mock the default configuration lookup
            default_config = SAMLConfiguration(
                site=self.site, slug='default', enabled=True,
                entity_id='https://default.example.com',
                org_info_str='{"en-US": {"url": "http://default.com", "displayname": "Default", "name": "default"}}'
            )
            mock_saml_current.return_value = default_config

            config = self.provider_config.get_current_saml_configuration()
            self.assertEqual(config.slug, 'default')

        elif scenario == 'none_found':
            # Test no configuration found
            self.provider_config.saml_configuration = None
            self.provider_config.save()

            # Mock that no default configuration is found
            mock_saml_current.return_value = None

            config = self.provider_config.get_current_saml_configuration()
            self.assertIsNone(config)

        mock_set_custom_attribute.assert_called_with(expected_attr_name, expected_attr_value)

    @override_settings(ENABLE_SAML_CONFIG_SIGNAL_HANDLERS=True)
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

    @ddt.data(
        (True, ['saml_config.signal_update', 'saml_config.signal_behavior'], ['updated_reference', 'active']),
        (False, ['saml_config.signal_behavior'], ['disabled_by_toggle:slug=test-config,id=', 'site_id=']),
    )
    @ddt.unpack
    @patch('common.djangoapps.third_party_auth.signals.handlers.set_custom_attribute')
    def test_toggle_signal_behavior(self, toggle_enabled, expected_attr_names, expected_attr_values, mock_set_custom_attribute):
        """Test signal handler behavior with toggle enabled/disabled."""
        with override_settings(ENABLE_SAML_CONFIG_SIGNAL_HANDLERS=toggle_enabled):
            # Update SAML configuration to trigger signal
            self.saml_config.entity_id = 'https://updated.example.com'
            self.saml_config.save()

            if toggle_enabled:
                # When enabled, should see both signal_update and signal_behavior
                expected_calls = [
                    call(expected_attr_names[0], expected_attr_values[0]),
                    call(expected_attr_names[1], expected_attr_values[1])
                ]
                mock_set_custom_attribute.assert_has_calls(expected_calls, any_order=True)
            else:
                # When disabled, should only see disabled behavior with detailed info
                mock_set_custom_attribute.assert_called_once()
                call_args = mock_set_custom_attribute.call_args[0]
                self.assertEqual(call_args[0], expected_attr_names[0])
                # Check that the disabled message contains expected components
                self.assertIn('disabled_by_toggle:slug=test-config', call_args[1])
                self.assertIn('site_id=', call_args[1])

    @ddt.data(
        (True, True),   # Toggle enabled, should set custom attributes
        (False, False), # Toggle disabled, should not set custom attributes
    )
    @ddt.unpack
    @patch('common.djangoapps.third_party_auth.models.set_custom_attribute')
    def test_toggle_custom_attributes(self, toggle_enabled, should_call_custom_attr, mock_set_custom_attribute):
        """Test that custom attributes respect the toggle setting."""
        with override_settings(ENABLE_SAML_CONFIG_SIGNAL_HANDLERS=toggle_enabled):
            config = self.provider_config.get_current_saml_configuration()
            self.assertIsNotNone(config)

            if should_call_custom_attr:
                mock_set_custom_attribute.assert_called_with('saml_config.using', 'direct')
            else:
                mock_set_custom_attribute.assert_not_called()


@ddt.ddt
class TestSAMLConfigurationManagementCommand(TestCase):
    """Test the SAML management command's fix-references functionality using DDT."""

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

    @ddt.data(
        (['--fix-references', '--dry-run'], True, 'outdated config'),   # Dry run mode
        (['--fix-references'], False, 'fixed'),                        # Actual fix mode
    )
    @ddt.unpack
    def test_command_handles_outdated_references(self, command_args, is_dry_run, expected_output, ):
        """Test that the command correctly handles outdated references."""
        from django.core.management import call_command
        from io import StringIO

        # Update SAML config to create new version
        self.saml_config.entity_id = 'https://updated.example.com'
        self.saml_config.save()
        new_config_id = self.saml_config.id

        # Set provider to old version
        old_configs = SAMLConfiguration.objects.filter(
            site=self.site, slug='test-config', enabled=False
        ).order_by('-change_date')

        if old_configs.exists():
            old_config = old_configs.first()
            self.provider_config.saml_configuration = old_config
            self.provider_config.save()

            # Run command
            out = StringIO()
            call_command('saml', *command_args, stdout=out)
            output = out.getvalue()

            # Verify output contains provider name
            self.assertIn('test-provider', output)

            # Verify behavior based on mode
            self.provider_config.refresh_from_db()
            if is_dry_run:
                self.assertIn(expected_output, output)
                # Should not actually fix in dry run
                self.assertNotEqual(self.provider_config.saml_configuration_id, new_config_id)
            else:
                # Should actually fix the reference
                self.assertEqual(self.provider_config.saml_configuration_id, new_config_id)
