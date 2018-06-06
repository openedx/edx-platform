"""
Django OAuth Toolkit scopes backend for the dot-dynamic-scopes package.
"""

from django.conf import settings
from django.utils import module_loading

from oauth2_provider.scopes import SettingsScopes


class DynamicScopes(SettingsScopes):
    """
    Scopes backend that provides scopes from a Django model.
    """
    def get_all_scopes(self):
        return settings.OAUTH2_PROVIDER['SCOPES']

    def get_available_scopes(self, application = None, request = None, *args, **kwargs):
        return list(self.get_all_scopes().keys())

