"""Unit tests for settings.py."""

from third_party_auth import provider, settings
from third_party_auth.tests import testutil


_ORIGINAL_AUTHENTICATION_BACKENDS = ('first_authentication_backend',)
_ORIGINAL_INSTALLED_APPS = ('first_installed_app',)
_ORIGINAL_MIDDLEWARE_CLASSES = ('first_middleware_class',)
_ORIGINAL_TEMPLATE_CONTEXT_PROCESSORS = ('first_template_context_preprocessor',)
_SETTINGS_MAP = {
    'AUTHENTICATION_BACKENDS': _ORIGINAL_AUTHENTICATION_BACKENDS,
    'INSTALLED_APPS': _ORIGINAL_INSTALLED_APPS,
    'MIDDLEWARE_CLASSES': _ORIGINAL_MIDDLEWARE_CLASSES,
    'TEMPLATE_CONTEXT_PROCESSORS': _ORIGINAL_TEMPLATE_CONTEXT_PROCESSORS,
    'FEATURES': {},
}


class SettingsUnitTest(testutil.TestCase):
    """Unit tests for settings management code."""

    # Allow access to protected methods (or module-protected methods) under
    # test. pylint: disable-msg=protected-access
    # Suppress sprurious no-member warning on fakes.
    # pylint: disable-msg=no-member

    def setUp(self):
        super(SettingsUnitTest, self).setUp()
        self.settings = testutil.FakeDjangoSettings(_SETTINGS_MAP)

    def test_apply_settings_adds_exception_middleware(self):
        settings.apply_settings({}, self.settings)
        for middleware_name in settings._MIDDLEWARE_CLASSES:
            self.assertIn(middleware_name, self.settings.MIDDLEWARE_CLASSES)

    def test_apply_settings_adds_fields_stored_in_session(self):
        settings.apply_settings({}, self.settings)
        self.assertEqual(settings._FIELDS_STORED_IN_SESSION, self.settings.FIELDS_STORED_IN_SESSION)

    def test_apply_settings_adds_third_party_auth_to_installed_apps(self):
        settings.apply_settings({}, self.settings)
        self.assertIn('third_party_auth', self.settings.INSTALLED_APPS)

    def test_apply_settings_enables_no_providers_and_completes_when_app_info_empty(self):
        settings.apply_settings({}, self.settings)
        self.assertEqual([], provider.Registry.enabled())

    def test_apply_settings_initializes_stubs_and_merges_settings_from_auth_info(self):
        for key in provider.GoogleOauth2.SETTINGS:
            self.assertFalse(hasattr(self.settings, key))

        auth_info = {
            provider.GoogleOauth2.NAME: {
                'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY': 'google_oauth2_key',
            },
        }
        settings.apply_settings(auth_info, self.settings)
        self.assertEqual('google_oauth2_key', self.settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY)
        self.assertIsNone(self.settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET)

    def test_apply_settings_prepends_auth_backends(self):
        self.assertEqual(_ORIGINAL_AUTHENTICATION_BACKENDS, self.settings.AUTHENTICATION_BACKENDS)
        settings.apply_settings({provider.GoogleOauth2.NAME: {}, provider.LinkedInOauth2.NAME: {}}, self.settings)
        self.assertEqual((
            provider.GoogleOauth2.get_authentication_backend(), provider.LinkedInOauth2.get_authentication_backend()) +
            _ORIGINAL_AUTHENTICATION_BACKENDS,
            self.settings.AUTHENTICATION_BACKENDS)

    def test_apply_settings_raises_value_error_if_provider_contains_uninitialized_setting(self):
        bad_setting_name = 'bad_setting'
        self.assertNotIn('bad_setting_name', provider.GoogleOauth2.SETTINGS)
        auth_info = {
            provider.GoogleOauth2.NAME: {
                bad_setting_name: None,
            },
        }
        with self.assertRaisesRegexp(ValueError, '^.*not initialized$'):
            settings.apply_settings(auth_info, self.settings)

    def test_apply_settings_turns_off_raising_social_exceptions(self):
        # Guard against submitting a conf change that's convenient in dev but
        # bad in prod.
        settings.apply_settings({}, self.settings)
        self.assertFalse(self.settings.SOCIAL_AUTH_RAISE_EXCEPTIONS)
