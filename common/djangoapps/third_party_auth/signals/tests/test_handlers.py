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


@ddt.ddt
class TestSAMLProviderConfigUpdates(TestCase):
    """
    Test SAML provider config updates based on SAML configuration changes.
    """

    def setUp(self):
        # Create test sites
        self.site1 = Site.objects.get_or_create(domain='test-site1.com', name='Site 1')[0]
        self.site2 = Site.objects.get_or_create(domain='test-site2.com', name='Site 2')[0]

        # Create SAML configs (same slug, different sites)
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

        # Create provider with NULL config (critical for fallback auth)
        self.null_provider = SAMLProviderConfigFactory(
            slug='null_provider',
            site=self.site1,
            saml_configuration=None
        )

    def _get_current_provider(self, slug):
        """
        Helper to get current version of provider by slug.
        """
        return SAMLProviderConfig.objects.current_set().get(slug=slug)

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
        # Case 1: Tests that NULL configurations are never updated by signal handler
        # Verifies that providers with NULL SAML config remain unchanged while valid configs are updated
        {
            'test_case': 'null_preserved',
            'description': 'NULL configuration preserved',
            'setup_data': {
                'create_valid_provider': True,
                'create_cross_site_provider': False,
                'create_site2_provider': False,
            },
        },
        # Case 2: Tests that signal handler only updates providers from same site
        # Verifies site isolation - only providers with configs from the updated site are changed
        {
            'test_case': 'site_isolation',
            'description': 'site isolation respected',
            'setup_data': {
                'create_valid_provider': False,
                'create_cross_site_provider': False,
                'create_site2_provider': True,
            },
        },
        # Case 3: Tests cross-site provider updates when SAML config site matches
        # Verifies that cross-site provider references are handled correctly
        {
            'test_case': 'cross_site',
            'description': 'cross-site provider updated',
            'setup_data': {
                'create_valid_provider': False,
                'create_cross_site_provider': True,
                'create_site2_provider': False,
            },
        },
    )
    @ddt.unpack
    @override_settings(ENABLE_SAML_CONFIG_SIGNAL_HANDLERS=True)
    def test_saml_provider_config_updates(self, test_case, description, setup_data):
        """
        Test SAML provider config updates under different scenarios.
        """
        if test_case == 'null_preserved':
            # Create provider with valid config
            valid_provider = SAMLProviderConfigFactory(
                slug='valid_provider',
                site=self.site1,
                saml_configuration=self.config1
            )

            # Trigger signal by creating new config
            new_config = self._create_new_config(self.site1)

            # Get current states
            current_valid = self._get_current_provider('valid_provider')
            current_null = self._get_current_provider('null_provider')

            # Verify: valid provider updated, NULL provider unchanged
            self.assertEqual(current_valid.saml_configuration_id, new_config.id)
            self.assertIsNone(current_null.saml_configuration_id)

        elif test_case == 'site_isolation':
            # Create providers on different sites
            site1_provider = SAMLProviderConfigFactory(
                slug='site1_provider',
                site=self.site1,
                saml_configuration=self.config1
            )
            site2_provider = SAMLProviderConfigFactory(
                slug='site2_provider',
                site=self.site2,
                saml_configuration=self.config2
            )
            original_site2_config_id = site2_provider.saml_configuration_id

            # Update only site1 config
            new_config = self._create_new_config(self.site1)

            # Get current states
            current_site1 = self._get_current_provider('site1_provider')
            current_site2 = self._get_current_provider('site2_provider')

            # Verify: only site1 provider updated, site2 provider unchanged
            self.assertEqual(current_site1.saml_configuration_id, new_config.id)
            self.assertEqual(current_site2.saml_configuration_id, original_site2_config_id)

        elif test_case == 'cross_site':
            # Create provider on site2 but referencing site1's config
            cross_site_provider = SAMLProviderConfigFactory(
                slug='cross_site_provider',
                site=self.site2,
                saml_configuration=self.config1
            )

            # Update site1's config
            new_config = self._create_new_config(self.site1)

            # Provider should be updated because its SAML config is from site1
            current_provider = self._get_current_provider('cross_site_provider')
            self.assertEqual(current_provider.saml_configuration_id, new_config.id)

    @override_settings(ENABLE_SAML_CONFIG_SIGNAL_HANDLERS=True)
    def test_null_configuration_preserved(self):
        """
        Test that NULL configurations are never updated by signal handler.
        """

        # Create provider with valid config
        valid_provider = SAMLProviderConfigFactory(
            slug='valid_provider',
            site=self.site1,
            saml_configuration=self.config1
        )

        # Trigger signal by creating new config
        new_config = self._create_new_config(self.site1)

        # Get current states
        current_valid = self._get_current_provider('valid_provider')
        current_null = self._get_current_provider('null_provider')

        # Verify: valid provider updated, NULL provider unchanged
        self.assertEqual(current_valid.saml_configuration_id, new_config.id)
        self.assertIsNone(current_null.saml_configuration_id)

    @override_settings(ENABLE_SAML_CONFIG_SIGNAL_HANDLERS=True)
    def test_site_isolation_respected(self):
        """
        Test that signal handler only updates providers from same site.
        """

        # Create providers on different sites
        site1_provider = SAMLProviderConfigFactory(
            slug='site1_provider',
            site=self.site1,
            saml_configuration=self.config1
        )
        site2_provider = SAMLProviderConfigFactory(
            slug='site2_provider',
            site=self.site2,
            saml_configuration=self.config2
        )
        original_site2_config_id = site2_provider.saml_configuration_id

        # Update only site1 config
        new_config = self._create_new_config(self.site1)

        # Get current states
        current_site1 = self._get_current_provider('site1_provider')
        current_site2 = self._get_current_provider('site2_provider')

        # Verify: only site1 provider updated, site2 provider unchanged
        self.assertEqual(current_site1.saml_configuration_id, new_config.id)
        self.assertEqual(current_site2.saml_configuration_id, original_site2_config_id)

    @override_settings(ENABLE_SAML_CONFIG_SIGNAL_HANDLERS=True)
    def test_cross_site_provider_updated(self):
        """
        Test provider gets updated when its SAML config's site matches, regardless of provider's site.
        """

        # Create provider on site2 but referencing site1's config
        cross_site_provider = SAMLProviderConfigFactory(
            slug='cross_site_provider',
            site=self.site2,
            saml_configuration=self.config1
        )

        # Update site1's config
        new_config = self._create_new_config(self.site1)

        # Provider should be updated because its SAML config is from site1
        current_provider = self._get_current_provider('cross_site_provider')
        self.assertEqual(current_provider.saml_configuration_id, new_config.id)
