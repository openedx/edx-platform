"""
Third-party auth provider configuration API.
"""


from django.contrib.sites.models import Site
from more_itertools import unique_everseen

from openedx.core.djangoapps.theming.helpers import get_current_request

from .models import (
    _LTI_BACKENDS,
    _PSA_OAUTH2_BACKENDS,
    _PSA_SAML_BACKENDS,
    LTIProviderConfig,
    OAuth2ProviderConfig,
    SAMLConfiguration,
    SAMLProviderConfig
)


# TODO Move to ConfigurationModel in django-config-models
def current_all(prov_cls, filters=None):
    """
    Like ConfigurationModel.current() but returns the current config in every
    partition as delineated by KEY_FIELDS -- and allows filters dict. (Does
    not include caching.)
    """

    def partition_key(obj):
        """Compute the partition key for this object."""
        return tuple(getattr(obj, k) for k in prov_cls.KEY_FIELDS)

    configs = prov_cls.objects.filter(**filters) if filters else prov_cls.objects.all()
    # Get the most recent record in each partition
    return unique_everseen(configs.order_by('-change_date'), partition_key)


class Registry(object):
    """
    API for querying third-party auth ProviderConfig objects.

    Providers must subclass ProviderConfig in order to be usable in the registry.
    """
    @classmethod
    def _enabled_providers(cls):
        """
        Generator returning all enabled providers of the current site.

        Provider configurations are partitioned on site + some key (backend
        name in the case of OAuth, slug for SAML, and consumer key for LTI).
        """
        site = Site.objects.get_current(get_current_request())

        # Note that site is added as an explicit filter. 'site_id' isn't in the
        # KEY_FIELDS for these models, but it should be; in the meantime, we
        # need to be careful not to let two configs belonging to two different
        # sites but with the same key "shadow" one another. That's easy here;
        # we just only ask for configs within the current request's site.

        # Get all OAuth2 provider configs for this site...
        for config in current_all(OAuth2ProviderConfig, {'site_id': site.pk}):
            # Ignore the config if it's disabled or we don't have a backend
            # class for it. (Not having a backend class for a config should
            # be pretty rare if it happens at all.)
            if config.enabled and config.backend_name in _PSA_OAUTH2_BACKENDS:
                yield config

        if SAMLConfiguration.is_enabled(site, 'default'):
            # ...followed by SAML configs, if feature is enabled...
            for config in current_all(SAMLProviderConfig, {'site_id': site.pk}):
                if config.enabled and config.backend_name in _PSA_SAML_BACKENDS:
                    yield config

        # ...and finally LTI configs
        for config in current_all(LTIProviderConfig, {'site_id': site.pk}):
            if config.enabled and config.backend_name in _LTI_BACKENDS:
                yield config

    @classmethod
    def enabled(cls):
        """Returns list of enabled providers."""
        return sorted(cls._enabled_providers(), key=lambda provider: provider.name)

    @classmethod
    def displayed_for_login(cls, tpa_hint=None):
        """
        Args:
            tpa_hint (string): An override used in certain third-party authentication
                scenarios that will cause the specified provider to be included in the
                set along with any providers matching the 'display_for_login' criteria.
                Note that 'provider_id' cannot have a value of None according to the
                current implementation.

        Returns:
            List of ProviderConfig entities
        """
        return [
            provider
            for provider in cls.enabled()
            if provider.display_for_login or provider.provider_id == tpa_hint
        ]

    @classmethod
    def get(cls, provider_id):
        """Gets provider by provider_id string if enabled, else None."""
        if not provider_id:
            return None
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
        backend on the current site.

        Example:
            >>> list(get_enabled_by_backend_name("tpa-saml"))
                [<SAMLProviderConfig>, <SAMLProviderConfig>]

        Args:
            backend_name: The name of a python-social-auth backend used by
                one or more providers.

        Yields:
            Instances of ProviderConfig.
        """
        for provider in cls._enabled_providers():
            if provider.backend_name == backend_name:
                yield provider
