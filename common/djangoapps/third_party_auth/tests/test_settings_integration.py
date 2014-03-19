"""
Integration tests for settings code.
"""

import mock
import unittest

from django.conf import settings

from third_party_auth import provider
from third_party_auth import settings as auth_settings
from third_party_auth.tests import testutil


class SettingsIntegrationTest(testutil.TestCase):
    """Integration tests of auth settings pipeline."""

    @unittest.skipUnless(
        testutil.AUTH_FEATURES_KEY in settings.FEATURES, testutil.AUTH_FEATURES_KEY + ' not in settings.FEATURES')
    def test_enable_third_party_auth_is_disabled_by_default(self):
        self.assertIs(False, settings.FEATURES.get(testutil.AUTH_FEATURES_KEY))

    @mock.patch.dict(settings.FEATURES, {'ENABLE_THIRD_PARTY_AUTH': True})
    def test_can_enable_google_oauth2(self):
        auth_settings.apply_settings({'Google': {'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY': 'google_key'}}, settings)
        self.assertEqual([provider.GoogleOauth2], provider.Registry.enabled())
        self.assertEqual('google_key', settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY)

    @mock.patch.dict(settings.FEATURES, {'ENABLE_THIRD_PARTY_AUTH': True})
    def test_can_enable_linkedin_oauth2(self):
        auth_settings.apply_settings({'LinkedIn': {'SOCIAL_AUTH_LINKEDIN_OAUTH2_KEY': 'linkedin_key'}}, settings)
        self.assertEqual([provider.LinkedInOauth2], provider.Registry.enabled())
        self.assertEqual('linkedin_key', settings.SOCIAL_AUTH_LINKEDIN_OAUTH2_KEY)
