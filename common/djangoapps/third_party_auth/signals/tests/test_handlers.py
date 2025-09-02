"""
Tests for SAML configuration signal handlers.
"""

import ddt
from unittest import mock
from unittest.mock import call
from django.test import TestCase, override_settings
from django.contrib.sites.models import Site
from common.djangoapps.third_party_auth.tests.factories import SAMLConfigurationFactory, SAMLProviderConfigFactory
from common.djangoapps.third_party_auth.models import SAMLProviderConfig


@ddt.ddt
class TestSAMLConfigurationSignalHandlers(TestCase):
    """
    Test effects of SAML configuration signal handlers.
    """
    def setUp(self):
        self.saml_config = SAMLConfigurationFactory(
            slug='test-config',
            entity_id='https://test.example.com',
            org_info_str='{"en-US": {"url": "http://test.com", "displayname": "Test", "name": "test"}}'
        )

        self.site1 = Site.objects.get_or_create(domain='test-site1.com', name='Site 1')[0]
        self.site2 = Site.objects.get_or_create(domain='test-site2.com', name='Site 2')[0]

        self.config1 = SAMLConfigurationFactory(
            site=self.site1,
            slug='default',
            entity_id='https://site1.com'
        )
        self.config2 = SAMLConfigurationFactory(
            site=self.site2,
            slug='default',
            entity_id='https://site2.com'
        )

        self.provider_with_null_saml_configuration = SAMLProviderConfigFactory(
            slug='null_saml_configuration',
            site=self.site1,
            saml_configuration=None
        )

        # Existing SAML config used by provider update tests
        self.existing_saml_config = SAMLConfigurationFactory(
            site=self.site1,
            slug='slug',
            entity_id='https://existing.example.com'
        )

    @ddt.data(
        # Case 1: Tests behavior when SAML config signal handlers are disabled
        # Verifies that basic attributes are set but no provider updates are attempted
        {
            'enabled': False,
            'simulate_error': False,
            'description': 'handlers disabled',
            'expected_calls': [
                call('saml_config_signal.enabled', False),
                call('saml_config_signal.new_config_id', 'CONFIG_ID'),
                call('saml_config_signal.slug', 'test-config'),
            ],
            'expected_call_count': 3,
        },
        # Case 2: Tests behavior when SAML config signal handlers are enabled
        # Verifies that attributes are set and provider updates are attempted successfully
        {
            'enabled': True,
            'simulate_error': False,
            'description': 'handlers enabled',
            'expected_calls': [
                call('saml_config_signal.enabled', True),
                call('saml_config_signal.new_config_id', 'CONFIG_ID'),
                call('saml_config_signal.slug', 'test-config'),
                call('saml_config_signal.updated_count', 0),
            ],
            'expected_call_count': 4,
        },
        # Case 3: Tests error handling when signal handlers are enabled but encounter an exception
        # Verifies that error information is properly captured when provider updates fail
        {
            'enabled': True,
            'simulate_error': True,
            'description': 'handlers enabled with exception',
            'expected_calls': [
                call('saml_config_signal.enabled', True),
                call('saml_config_signal.new_config_id', 'CONFIG_ID'),
                call('saml_config_signal.slug', 'test-config'),
            ],
            'expected_call_count': 4,  # includes error_message call
            'error_message': 'Test error',
        },
    )
    @ddt.unpack
    @mock.patch('common.djangoapps.third_party_auth.signals.handlers.set_custom_attribute')
    def test_saml_config_signal_handlers(
            self, mock_set_custom_attribute, enabled, simulate_error,
            description, expected_calls, expected_call_count, error_message=None):
        """
        Test SAML configuration signal handlers under different conditions.
        """
        with override_settings(ENABLE_SAML_CONFIG_SIGNAL_HANDLERS=enabled):
            if simulate_error:
                # Simulate an exception in the provider config update logic
                with mock.patch(
                    'common.djangoapps.third_party_auth.models.SAMLProviderConfig.objects.current_set',
                    side_effect=Exception(error_message)
                ):
                    self.saml_config.entity_id = 'https://updated.example.com'
                    self.saml_config.save()
            else:
                self.saml_config.entity_id = 'https://updated.example.com'
                self.saml_config.save()

            expected_calls_with_id = []
            for call_obj in expected_calls:
                args = list(call_obj[1])
                if args[1] == 'CONFIG_ID':
                    args[1] = self.saml_config.id
                expected_calls_with_id.append(call(args[0], args[1]))

            # Verify expected calls were made
            mock_set_custom_attribute.assert_has_calls(expected_calls_with_id, any_order=False)

            # Verify total call count
            assert mock_set_custom_attribute.call_count == expected_call_count, (
                f"Expected {expected_call_count} calls for {description}, "
                f"got {mock_set_custom_attribute.call_count}"
            )

            # If error is expected, verify error message was logged
            if error_message:
                mock_set_custom_attribute.assert_any_call(
                    'saml_config_signal.error_message',
                    mock.ANY
                )
                error_calls = [
                    call for call in mock_set_custom_attribute.mock_calls
                    if call[1][0] == 'saml_config_signal.error_message'
                ]
                assert error_message in error_calls[0][1][1], (
                    f"Expected '{error_message}' in error message for {description}, "
                    f"got: {error_calls[0][1][1]}"
                )

    def _get_current_provider(self, slug):
        """
        Helper to get current version of provider by slug.
        """
        return SAMLProviderConfig.objects.current_set().get(slug=slug)

    def _get_site(self, site_id):
        """
        Helper to get site by ID (1 = site1, 2 = site2).
        """
        return self.site1 if site_id == 1 else self.site2

    def _create_new_config(self, site, slug='default'):
        """
        Helper to create new SAML config and trigger signal.
        """
        return SAMLConfigurationFactory(
            site=site,
            slug=slug,
            entity_id=f'https://{site.domain}/updated'
        )

    @ddt.data(
        # Args: provider_site_id, provider_slug, signal_saml_site_id, signal_saml_slug, is_provider_updated
        # All tests: provider's saml_configuration has site_id=1, slug='slug'
        #
        # Signal matches provider's saml config and should update
        (1, 'slug', 1, 'slug', True),       # Same site, same slug
        (2, 'slug', 1, 'slug', True),       # Cross-site provider, matching saml config
        (1, 'provider-slug', 1, 'slug', True),  # Different provider slug, matching saml config
        # Signal does not match provider's saml config and should not update
        (1, 'slug', 2, 'slug', False),      # Different saml config site
        (2, 'slug', 2, 'slug', False),      # Different saml config site (cross-site)
        (1, 'provider-slug', 1, 'provider-slug', False),  # Different saml config slug
        (2, 'provider-slug', 1, 'provider-slug', False),  # Different saml config slug (cross-site)
    )
    @ddt.unpack
    @override_settings(ENABLE_SAML_CONFIG_SIGNAL_HANDLERS=True)
    def test_saml_provider_config_updates(self, provider_site_id, provider_slug,
                                          signal_saml_site_id, signal_saml_slug, is_provider_updated):
        """
        Test SAML provider config updates under different scenarios.

        Tests that providers are updated only when the signal's SAML configuration
        matches the provider's existing SAML configuration (by site and slug).
        """
        provider_site = self._get_site(provider_site_id)
        signal_saml_site = self._get_site(signal_saml_site_id)

        provider = SAMLProviderConfigFactory(
            slug=provider_slug,
            site=provider_site,
            saml_configuration=self.existing_saml_config
        )
        original_config_id = provider.saml_configuration_id

        new_saml_config = SAMLConfigurationFactory(
            site=signal_saml_site,
            slug=signal_saml_slug,
            entity_id='https://new.example.com'
        )

        current_provider = self._get_current_provider(provider_slug)

        if is_provider_updated:
            self.assertEqual(current_provider.saml_configuration_id, new_saml_config.id,
                             f"Provider should be updated when signal SAML config matches")
        else:
            self.assertEqual(current_provider.saml_configuration_id, original_config_id,
                             f"Provider should NOT be updated when signal SAML config doesn't match")

    @ddt.data(
        # Args: provider_site_id, provider_slug, signal_saml_site_id, signal_saml_slug
        #
        # All tests: provider's saml config is None and should never be updated
        (1, 'slug', 1, 'default'),
        (1, 'default', 1, 'default'),
        (2, 'slug', 1, 'default'),
        (2, 'default', 2, 'default'),
    )
    @ddt.unpack
    @override_settings(ENABLE_SAML_CONFIG_SIGNAL_HANDLERS=True)
    def test_saml_provider_with_null_config_not_updated(self, provider_site_id, provider_slug,
                                                        signal_saml_site_id, signal_saml_slug):
        """
        Test that providers with NULL SAML configuration are never updated by signal handler.

        This is critical for fallback authentication scenarios where providers
        intentionally have no SAML configuration.
        """
        provider_site = self._get_site(provider_site_id)
        signal_saml_site = self._get_site(signal_saml_site_id)

        null_provider = SAMLProviderConfigFactory(
            slug=provider_slug,
            site=provider_site,
            saml_configuration=None
        )

        new_saml_config = SAMLConfigurationFactory(
            site=signal_saml_site,
            slug=signal_saml_slug,
            entity_id='https://new.example.com'
        )

        current_provider = self._get_current_provider(provider_slug)
        self.assertIsNone(current_provider.saml_configuration_id,
                          "Provider with NULL SAML config should never be updated")
