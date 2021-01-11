"""Unit tests for settings.py."""


import unittest

from mock import patch
from common.djangoapps.third_party_auth import provider, settings
from common.djangoapps.third_party_auth.tests import testutil
from common.djangoapps.third_party_auth.tests.utils import skip_unless_thirdpartyauth
_ORIGINAL_AUTHENTICATION_BACKENDS = ['first_authentication_backend']
_ORIGINAL_INSTALLED_APPS = ['first_installed_app']
_ORIGINAL_MIDDLEWARE_CLASSES = ['first_middleware_class']
_ORIGINAL_TEMPLATE_CONTEXT_PROCESSORS = ['first_template_context_preprocessor']
_SETTINGS_MAP = {
    'AUTHENTICATION_BACKENDS': _ORIGINAL_AUTHENTICATION_BACKENDS,
    'INSTALLED_APPS': _ORIGINAL_INSTALLED_APPS,
    'MIDDLEWARE': _ORIGINAL_MIDDLEWARE_CLASSES,
    'TEMPLATES': [{
        'OPTIONS': {
            'context_processors': _ORIGINAL_TEMPLATE_CONTEXT_PROCESSORS
        }
    }],
    'FEATURES': {},
}
_SETTINGS_MAP['DEFAULT_TEMPLATE_ENGINE'] = _SETTINGS_MAP['TEMPLATES'][0]


class SettingsUnitTest(testutil.TestCase):
    """Unit tests for settings management code."""

    # Suppress spurious no-member warning on fakes.
    # pylint: disable=no-member

    def setUp(self):
        super(SettingsUnitTest, self).setUp()
        self.settings = testutil.FakeDjangoSettings(_SETTINGS_MAP)

    def test_apply_settings_adds_exception_middleware(self):
        settings.apply_settings(self.settings)
        self.assertIn('common.djangoapps.third_party_auth.middleware.ExceptionMiddleware', self.settings.MIDDLEWARE)

    def test_apply_settings_adds_fields_stored_in_session(self):
        settings.apply_settings(self.settings)
        self.assertEqual(['auth_entry', 'next'], self.settings.FIELDS_STORED_IN_SESSION)

    @skip_unless_thirdpartyauth()
    def test_apply_settings_enables_no_providers_by_default(self):
        # Providers are only enabled via ConfigurationModels in the database
        settings.apply_settings(self.settings)
        self.assertEqual([], provider.Registry.enabled())

    def test_apply_settings_turns_off_raising_social_exceptions(self):
        # Guard against submitting a conf change that's convenient in dev but
        # bad in prod.
        settings.apply_settings(self.settings)
        self.assertFalse(self.settings.SOCIAL_AUTH_RAISE_EXCEPTIONS)

    def test_apply_settings_turns_off_redirect_sanitization(self):
        settings.apply_settings(self.settings)
        self.assertFalse(self.settings.SOCIAL_AUTH_SANITIZE_REDIRECTS)

    def test_apply_settings_avoids_default_username_check(self):
        # Avoid the default username check where non-ascii characters are not
        # allowed when unicode username is enabled
        settings.apply_settings(self.settings)
        self.assertTrue(self.settings.SOCIAL_AUTH_CLEAN_USERNAMES)   # verify default behavior
        with patch.dict('django.conf.settings.FEATURES', {'ENABLE_UNICODE_USERNAME': True}):
            settings.apply_settings(self.settings)
            self.assertFalse(self.settings.SOCIAL_AUTH_CLEAN_USERNAMES)
