"""
Slightly customized python-social-auth backend for SAML 2.0 support
"""
from social.backends.saml import SAMLAuth


class SAMLAuthBackend(SAMLAuth):  # pylint: disable=abstract-method
    """
    Customized version of SAMLAuth that gets the list of IdPs from third_party_auth's list of
    enabled providers.
    """
    name = "tpa-saml"

    def get_idp(self, idp_name):
        """ Given the name of an IdP, get a SAMLIdentityProvider instance """
        from .models import SAMLProviderConfig
        return SAMLProviderConfig.current(idp_name).get_config()

    def setting(self, name, default=None):
        """ Get a setting, from SAMLConfiguration """
        if not hasattr(self, '_config'):
            from .models import SAMLConfiguration
            self._config = SAMLConfiguration.current()  # pylint: disable=attribute-defined-outside-init
        if not self._config.enabled:
            from django.core.exceptions import ImproperlyConfigured
            raise ImproperlyConfigured("SAML Authentication is not enabled.")
        try:
            return self._config.get_setting(name)
        except KeyError:
            return self.strategy.setting(name, default)
