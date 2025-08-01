"""
Tests for SAML configuration signal handlers.
"""

import ddt
from unittest import mock
from unittest.mock import call
from django.test import TestCase, override_settings
from common.djangoapps.third_party_auth.tests.factories import SAMLConfigurationFactory


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
                error_calls = [
                    call for call in mock_set_custom_attribute.mock_calls
                    if call[1][0] == 'saml_config_signal.error_message'
                ]
                assert error_calls, (
                    f"Expected 'saml_config_signal.error_message' call for {description}, "
                    f"got: {mock_set_custom_attribute.mock_calls}"
                )
                assert error_message in error_calls[0][1][1], (
                    f"Expected '{error_message}' in error message for {description}, "
                    f"got: {error_calls[0][1][1]}"
                )
