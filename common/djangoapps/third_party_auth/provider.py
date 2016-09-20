"""
Third-party auth provider configuration API.
"""
from .models import (
    OAuth2ProviderConfig, SAMLConfiguration, SAMLProviderConfig, LTIProviderConfig,
    _PSA_OAUTH2_BACKENDS, _PSA_SAML_BACKENDS, _LTI_BACKENDS,
)


class Registry(object):
    """
    API for querying third-party auth ProviderConfig objects.

    Providers must subclass ProviderConfig in order to be usable in the registry.
    """
    @classmethod
    def _enabled_providers(cls):
        """ Helper method to iterate over all providers """
        for backend_name in _PSA_OAUTH2_BACKENDS:
            provider = OAuth2ProviderConfig.current(backend_name)
            if provider.enabled:
                yield provider
        if SAMLConfiguration.is_enabled():
            idp_slugs = SAMLProviderConfig.key_values('idp_slug', flat=True)
            for idp_slug in idp_slugs:
                provider = SAMLProviderConfig.current(idp_slug)
                if provider.enabled and provider.backend_name in _PSA_SAML_BACKENDS:
                    yield provider
        for consumer_key in LTIProviderConfig.key_values('lti_consumer_key', flat=True):
            provider = LTIProviderConfig.current(consumer_key)
            if provider.enabled and provider.backend_name in _LTI_BACKENDS:
                yield provider

    @classmethod
    def enabled(cls):
        """Returns list of enabled providers."""
        return sorted(cls._enabled_providers(), key=lambda provider: provider.name)

    @classmethod
    def displayed_for_login(cls):
        """Returns list of providers that can be used to initiate logins in the UI"""
        return [provider for provider in cls.enabled() if provider.display_for_login]

    @classmethod
    def get(cls, provider_id):
        """Gets provider by provider_id string if enabled, else None."""
        if '-' not in provider_id:  # Check format - see models.py:ProviderConfig
            raise ValueError("Invalid provider_id. Expect something like oa2-google")
        try:
            return next(provider for provider in cls._enabled_providers() if provider.provider_id == provider_id)
        except StopIteration:
            return None

    @classmethod
    def get_from_pipeline(cls, running_pipeline):
        """Gets the provider that is being used for the specified pipeline (or None).

        Args:
            running_pipeline: The python-social-auth pipeline being used to
                authenticate a user.

        Returns:
            An instance of ProviderConfig or None.
        """
        for enabled in cls._enabled_providers():
            if enabled.is_active_for_pipeline(running_pipeline):
                return enabled

    @classmethod
    def get_enabled_by_backend_name(cls, backend_name):
        """Generator returning all enabled providers that use the specified
        backend.

        Example:
            >>> list(get_enabled_by_backend_name("tpa-saml"))
                [<SAMLProviderConfig>, <SAMLProviderConfig>]

        Args:
            backend_name: The name of a python-social-auth backend used by
                one or more providers.

        Yields:
            Instances of ProviderConfig.
        """
        if backend_name in _PSA_OAUTH2_BACKENDS:
            provider = OAuth2ProviderConfig.current(backend_name)
            if provider.enabled:
                yield provider
        elif backend_name in _PSA_SAML_BACKENDS and SAMLConfiguration.is_enabled():
            idp_names = SAMLProviderConfig.key_values('idp_slug', flat=True)
            for idp_name in idp_names:
                provider = SAMLProviderConfig.current(idp_name)
                if provider.backend_name == backend_name and provider.enabled:
                    yield provider
        elif backend_name in _LTI_BACKENDS:
            for consumer_key in LTIProviderConfig.key_values('lti_consumer_key', flat=True):
                provider = LTIProviderConfig.current(consumer_key)
                if provider.backend_name == backend_name and provider.enabled:
                    yield provider
