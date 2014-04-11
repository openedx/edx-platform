"""Integration tests for settings.py."""

from django.conf import settings

from third_party_auth import provider
from third_party_auth import settings as auth_settings
from third_party_auth.tests import testutil


class SettingsIntegrationTest(testutil.TestCase):
    """Integration tests of auth settings pipeline.

    Note that ENABLE_THIRD_PARTY_AUTH is True in lms/envs/test.py and False in
    cms/envs/test.py. This implicitly gives us coverage of the full settings
    mechanism with both values, so we do not have explicit test methods as they
    are superfluous.
    """

    def test_can_enable_google_oauth2(self):
        auth_settings.apply_settings({'Google': {'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY': 'google_key'}}, settings)
        self.assertEqual([provider.GoogleOauth2], provider.Registry.enabled())
        self.assertEqual('google_key', settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY)

    def test_can_enable_linkedin_oauth2(self):
        auth_settings.apply_settings({'LinkedIn': {'SOCIAL_AUTH_LINKEDIN_OAUTH2_KEY': 'linkedin_key'}}, settings)
        self.assertEqual([provider.LinkedInOauth2], provider.Registry.enabled())
        self.assertEqual('linkedin_key', settings.SOCIAL_AUTH_LINKEDIN_OAUTH2_KEY)
