"""
Custom Django OAuth Toolkit scopes backends.
"""

from oauth2_provider.scopes import SettingsScopes


class ApplicationModelScopes(SettingsScopes):
    """
    Scopes backend that determines available scopes using the ScopedApplication model.
    """
    def get_available_scopes(self, application=None, request=None, *args, **kwargs):
        """ Returns valid scopes configured for the given application. """
        application_scopes = getattr(application, 'scopes', None)
        if application_scopes:
            default_scopes = self.get_default_scopes()
            all_scopes = self.get_all_scopes().keys()
            return set(application_scopes + default_scopes).intersection(all_scopes)
        else:
            return super(ApplicationModelScopes, self).get_available_scopes(application, request, *args, **kwargs)
