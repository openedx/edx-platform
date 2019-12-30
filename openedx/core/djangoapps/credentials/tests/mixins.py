"""Mixins for use during testing."""


from openedx.core.djangoapps.credentials.models import CredentialsApiConfig


class CredentialsApiConfigMixin(object):
    """ Utilities for working with Credentials configuration during testing."""

    CREDENTIALS_DEFAULTS = {
        'enabled': True,
        'internal_service_url': 'http://internal.credentials.org/',
        'public_service_url': 'http://public.credentials.org/',
        'enable_learner_issuance': True,
        'enable_studio_authoring': True,
        'cache_ttl': 0,
    }

    def create_credentials_config(self, **kwargs):
        """ Creates a new CredentialsApiConfig with DEFAULTS, updated with any
        provided overrides.
        """
        fields = dict(self.CREDENTIALS_DEFAULTS, **kwargs)
        CredentialsApiConfig(**fields).save()

        return CredentialsApiConfig.current()
