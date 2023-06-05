

from django.apps import AppConfig
from django.conf import settings


class ThirdPartyAuthConfig(AppConfig):
    name = 'common.djangoapps.third_party_auth'
    verbose_name = "Third-party authentication"

    def ready(self):
        # To override the settings before loading social_django.
        if settings.FEATURES.get('ENABLE_THIRD_PARTY_AUTH', False):
            self._enable_third_party_auth()

    def _enable_third_party_auth(self):
        """
        Enable the use of third_party_auth, which allows users to sign in to edX
        using other identity providers. For configuration details, see
        common/djangoapps/third_party_auth/settings.py.
        """
        from common.djangoapps.third_party_auth import settings as auth_settings
        auth_settings.apply_settings(settings)
