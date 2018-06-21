"""
Custom Django OAuth Toolkit scopes backends.
"""

from oauth2_provider.scopes import SettingsScopes

from openedx.core.djangoapps.oauth_dispatch.models import ApplicationAccess


class ApplicationModelScopes(SettingsScopes):
    """
    Scopes backend that determines available scopes using the ScopedApplication model.
    """
    def get_available_scopes(self, application=None, request=None, *args, **kwargs):
        """ Returns valid scopes configured for the given application. """
        try:
            application_scopes = ApplicationAccess.objects.get(application=application).scopes
            default_scopes = self.get_default_scopes()
            all_scopes = self.get_all_scopes().keys()
            return set(application_scopes + default_scopes).intersection(all_scopes)
        except ApplicationAccess.DoesNotExist:
            return super(ApplicationModelScopes, self).get_default_scopes(application, request, *args, **kwargs)
