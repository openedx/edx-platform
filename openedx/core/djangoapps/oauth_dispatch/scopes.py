"""
Custom Django OAuth Toolkit scopes backends.
"""


from oauth2_provider.scopes import SettingsScopes

from openedx.core.djangoapps.oauth_dispatch.models import ApplicationAccess


class ApplicationModelScopes(SettingsScopes):
    """
    Scopes backend that determines available scopes using the ApplicationAccess model.
    """
    def get_available_scopes(self, application=None, request=None, *args, **kwargs):  # lint-amnesty, pylint: disable=keyword-arg-before-vararg
        """ Returns valid scopes configured for the given application. """
        try:
            application_scopes = ApplicationAccess.get_scopes(application)
        except ApplicationAccess.DoesNotExist:
            application_scopes = []

        default_scopes = self.get_default_scopes()
        all_scopes = list(self.get_all_scopes().keys())
        return set(application_scopes + default_scopes).intersection(all_scopes)
