"""
A custom Strategy for python-social-auth that allows us to fetch configuration from
ConfigurationModels rather than django.settings
"""
from .models import OAuth2ProviderConfig
from .pipeline import AUTH_ENTRY_CUSTOM
from social.backends.oauth import OAuthAuth
from social.strategies.django_strategy import DjangoStrategy


class ConfigurationModelStrategy(DjangoStrategy):
    """
    A DjangoStrategy customized to load settings from ConfigurationModels
    for upstream python-social-auth backends that we cannot otherwise modify.
    """
    def setting(self, name, default=None, backend=None):
        """
        Load the setting from a ConfigurationModel if possible, or fall back to the normal
        Django settings lookup.

        OAuthAuth subclasses will call this method for every setting they want to look up.
        SAMLAuthBackend subclasses will call this method only after first checking if the
            setting 'name' is configured via SAMLProviderConfig.
        LTIAuthBackend subclasses will call this method only after first checking if the
            setting 'name' is configured via LTIProviderConfig.
        """
        if isinstance(backend, OAuthAuth):
            provider_config = OAuth2ProviderConfig.current(backend.name)
            if not provider_config.enabled:
                raise Exception("Can't fetch setting of a disabled backend/provider.")
            try:
                return provider_config.get_setting(name)
            except KeyError:
                pass

        # special case handling of login error URL if we're using a custom auth entry point:
        if name == 'LOGIN_ERROR_URL':
            auth_entry = self.request.session.get('auth_entry')
            if auth_entry and auth_entry in AUTH_ENTRY_CUSTOM:
                error_url = AUTH_ENTRY_CUSTOM[auth_entry].get('error_url')
                if error_url:
                    return error_url

        # At this point, we know 'name' is not set in a [OAuth2|LTI|SAML]ProviderConfig row.
        # It's probably a global Django setting like 'FIELDS_STORED_IN_SESSION':
        return super(ConfigurationModelStrategy, self).setting(name, default, backend)

    def request_host(self):
        """
        Host in use for this request
        """
        # TODO: this override is a temporary measure until upstream python-social-auth patch is merged:
        # https://github.com/omab/python-social-auth/pull/741
        if self.setting('RESPECT_X_FORWARDED_HEADERS', False):
            forwarded_host = self.request.META.get('HTTP_X_FORWARDED_HOST')
            if forwarded_host:
                return forwarded_host

        return super(ConfigurationModelStrategy, self).request_host()

    def request_port(self):
        """
        Port in use for this request
        """
        # TODO: this override is a temporary measure until upstream python-social-auth patch is merged:
        # https://github.com/omab/python-social-auth/pull/741
        if self.setting('RESPECT_X_FORWARDED_HEADERS', False):
            forwarded_port = self.request.META.get('HTTP_X_FORWARDED_PORT')
            if forwarded_port:
                return forwarded_port

        return super(ConfigurationModelStrategy, self).request_port()
