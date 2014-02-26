"""
Unit tests for settings code.
"""

import copy
import unittest

from auth import provider
from auth import settings


_ORIGINAL_AUTHENTICATION_BACKENDS = ('first_authentication_backend',)
_ORIGINAL_INSTALLED_APPS = ('first_installed_app',)
_ORIGINAL_TEMPLATE_CONTEXT_PROCESSORS = ('first_template_context_preprocessor',)
_FAKE_SETTINGS = {
    'AUTHENTICATION_BACKENDS': _ORIGINAL_AUTHENTICATION_BACKENDS,
    'INSTALLED_APPS': _ORIGINAL_INSTALLED_APPS,
    'TEMPLATE_CONTEXT_PROCESSORS': _ORIGINAL_TEMPLATE_CONTEXT_PROCESSORS,
}


class SettingsUnitTest(unittest.TestCase):
    """Unit tests for settings management code."""

    # Allow descriptive test method names. pylint: disable-msg=invalid-name
    # Allow access to protected methods (or module-protected methods) under test: pylint: disable-msg=protected-access
    def setUp(self):
        self.settings = copy.deepcopy(_FAKE_SETTINGS)
        provider.Registry._reset()
        super(SettingsUnitTest, self).setUp()

    def tearDown(self):
        provider.Registry._reset()
        super(SettingsUnitTest, self).tearDown()

    def test_patch_enables_no_providers_and_completes_when_app_info_empty(self):
        auth_info = {}
        settings.patch(auth_info, self.settings)
        self.assertEqual([], provider.Registry.enabled())

    def test_patch_initializes_stubs_and_merges_settings_from_auth_info(self):
        for key in provider.GoogleOauth2.SETTINGS:
            self.assertNotIn(key, self.settings)

        auth_info = {
            provider.GoogleOauth2.NAME: {
                'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY': 'google_oauth2_key',
            },
        }
        settings.patch(auth_info, self.settings)
        self.assertEqual('google_oauth2_key', self.settings['SOCIAL_AUTH_GOOGLE_OAUTH2_KEY'])
        self.assertIsNone(self.settings['SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET'])

    def test_patch_raises_value_error_if_provider_contains_uninitialized_setting(self):
        bad_setting_name = 'bad_setting'
        self.assertNotIn('bad_setting_name', provider.GoogleOauth2.SETTINGS)
        auth_info = {
            provider.GoogleOauth2.NAME: {
                bad_setting_name: None,
            },
        }
        with self.assertRaises(ValueError) as e:
            settings.patch(auth_info, self.settings)

        self.assertIn(bad_setting_name + ' not initialized', e.exception.message)
