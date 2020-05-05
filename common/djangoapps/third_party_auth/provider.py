"""
Third-party auth provider configuration API.
"""


from django.contrib.sites.models import Site
import edx_django_utils.monitoring as monitoring_utils
from more_itertools import unique_everseen

from openedx.core.djangoapps.theming.helpers import get_current_request
from openedx.core.lib.cache_utils import request_cached

from .models import (
    _LTI_BACKENDS,
    _PSA_OAUTH2_BACKENDS,
    _PSA_SAML_BACKENDS,
    LTIProviderConfig,
    OAuth2ProviderConfig,
    SAMLConfiguration,
    SAMLProviderConfig
)

CACHE_NAMESPACE = 'third_party_auth.provider'


@request_cached(namespace=CACHE_NAMESPACE)
def current_configs_for_site(provider_cls, site_id):
    """
    Like ConfigurationModel.current() but returns the current config in every
    partition as delineated by KEY_FIELDS, but only looking at configs in the
    specified site.

    This is a hack to support these provider configs, which do not include site
    in their KEY_FIELDS but need to be partitioned on site. See comment in
    ``_enabled_providers`` for more details.
    """

    def partition_key(obj):
        """Compute the partition key for this object."""
        return tuple(getattr(obj, k) for k in provider_cls.KEY_FIELDS)

    configs = provider_cls.objects.filter(site_id=str(site_id))
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
        try:
            old_values = set(cls._enabled_providers_old())
        except:
            # Make sure we have an error baseline to compare to
            monitoring_utils.increment("temp_tpa_enabled_all_dark_launch_old_threw")
            raise

        # Dark launch call and metrics
        try:
            new_values = set(cls._enabled_providers_new())

            try:
                if old_values != new_values:
                    data = "old[%s]new[%s]" % (
                        ','.join([str(p.id) for p in old_values]),
                        ','.join([str(p.id) for p in new_values]))
                    monitoring_utils.set_custom_metric("temp_tpa_enabled_all_dark_launch_mismatch", data)
            except:  # pylint: disable=bare-except
                pass
        except:  # pylint: disable=bare-except
            monitoring_utils.increment("temp_tpa_enabled_all_dark_launch_new_threw")

        # Could return old_values, but lets keep it a generator for consistency
        for config in old_values:
            yield config

    @classmethod
    def _enabled_providers_old(cls):
        """Old implementation of _enabled_providers"""
        oauth2_backend_names = OAuth2ProviderConfig.key_values('backend_name', flat=True)
        for oauth2_backend_name in oauth2_backend_names:
            provider = OAuth2ProviderConfig.current(oauth2_backend_name)
            if provider.enabled_for_current_site and provider.backend_name in _PSA_OAUTH2_BACKENDS:
                yield provider
        if SAMLConfiguration.is_enabled(Site.objects.get_current(get_current_request()), 'default'):
            idp_slugs = SAMLProviderConfig.key_values('slug', flat=True)
            for idp_slug in idp_slugs:
                provider = SAMLProviderConfig.current(idp_slug)
                if provider.enabled_for_current_site and provider.backend_name in _PSA_SAML_BACKENDS:
                    yield provider
        for consumer_key in LTIProviderConfig.key_values('lti_consumer_key', flat=True):
            provider = LTIProviderConfig.current(consumer_key)
            if provider.enabled_for_current_site and provider.backend_name in _LTI_BACKENDS:
                yield provider

    @classmethod
    def _enabled_providers_new(cls):
        """New implementation of _enabled_providers for dark launch"""
        site = Site.objects.get_current(get_current_request())

        # Note that site is added as an explicit filter. 'site_id' isn't in the
        # KEY_FIELDS for these models, but it should be, since we want "the most
        # recent version of the config" to be most recent for a given key *and*
        # site. Since site is not in KEY_FIELDS, looking up a config by just its
        # key could result in finding a config for a different site. (The
        # previous code here would then have returned nothing, having had a
        # site-filtering step.) In short, we need to be careful not to let two
        # configs belonging to two different sites but with the same key
        # "shadow" one another.
        #
        # It's not clear if we can safely add site_id to the KEY_FIELDS, and
        # it's also not clear if we're even going to want to keep support for
        # sites here long term, so in the meantime we just only ask for
        # configs within the current request's site.

        # Get all OAuth2 provider configs for this site...
        for config in current_configs_for_site(OAuth2ProviderConfig, site.pk):
            # Ignore the config if it's disabled or we don't have a backend
            # class for it. (Not having a backend class for a config should
            # be pretty rare if it happens at all.)
            if config.enabled and config.backend_name in _PSA_OAUTH2_BACKENDS:
                yield config

        if SAMLConfiguration.is_enabled(site, 'default'):
            # ...followed by SAML configs, if feature is enabled...
            for config in current_configs_for_site(SAMLProviderConfig, site.pk):
                if config.enabled and config.backend_name in _PSA_SAML_BACKENDS:
                    yield config

        # ...and finally LTI configs
        for config in current_configs_for_site(LTIProviderConfig, site.pk):
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
        try:
            old_values = set(cls._get_enabled_by_backend_name_old(backend_name))
        except:
            # Make sure we have an error baseline to compare to
            monitoring_utils.increment("temp_tpa_by_backend_dark_launch_old_threw")
            raise

        # Dark launch call and metrics
        try:
            new_values = set(cls._get_enabled_by_backend_name_new(backend_name))

            try:
                if old_values != new_values:
                    data = "backend[%s]old[%s]new[%s]" % (
                        backend_name,
                        ','.join([str(p.id) for p in old_values]),
                        ','.join([str(p.id) for p in new_values]))
                    monitoring_utils.set_custom_metric("temp_tpa_by_backend_dark_launch_mismatch", data)
            except:  # pylint: disable=bare-except
                pass
        except:  # pylint: disable=bare-except
            monitoring_utils.increment("temp_tpa_by_backend_dark_launch_new_threw")

        # Could return old_values, but lets keep it a generator for consistency
        for config in old_values:
            yield config

    @classmethod
    def _get_enabled_by_backend_name_old(cls, backend_name):
        """Old implementation of get_enabled_by_backend_name"""
        if backend_name in _PSA_OAUTH2_BACKENDS:
            oauth2_backend_names = OAuth2ProviderConfig.key_values('backend_name', flat=True)
            for oauth2_backend_name in oauth2_backend_names:
                provider = OAuth2ProviderConfig.current(oauth2_backend_name)
                if provider.backend_name == backend_name and provider.enabled_for_current_site:
                    yield provider
        elif backend_name in _PSA_SAML_BACKENDS and SAMLConfiguration.is_enabled(
                Site.objects.get_current(get_current_request()), 'default'):
            idp_names = SAMLProviderConfig.key_values('slug', flat=True)
            for idp_name in idp_names:
                provider = SAMLProviderConfig.current(idp_name)
                if provider.backend_name == backend_name and provider.enabled_for_current_site:
                    yield provider
        elif backend_name in _LTI_BACKENDS:
            for consumer_key in LTIProviderConfig.key_values('lti_consumer_key', flat=True):
                provider = LTIProviderConfig.current(consumer_key)
                if provider.backend_name == backend_name and provider.enabled_for_current_site:
                    yield provider

    @classmethod
    def _get_enabled_by_backend_name_new(cls, backend_name):
        """New implementation of get_enabled_by_backend_name for dark launch"""
        for provider in cls._enabled_providers():
            if provider.backend_name == backend_name:
                yield provider
