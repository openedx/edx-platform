"""Third-party auth provider definitions.

Loaded by Django's settings mechanism. Consequently, this module must not
invoke the Django armature.
"""


class BaseProvider(object):
    """Abstract base class for third-party auth providers.

    All providers must subclass BaseProvider -- otherwise, they cannot be put
    in the provider Registry.
    """

    # String. Dot-delimited module.Class. The name of the backend
    # implementation to load.
    AUTHENTICATION_BACKEND = None
    # String. User-facing name of the provider. Must be unique across all
    # enabled providers.
    NAME = None

    # Dict of string -> object. Settings that will be merged into Django's
    # settings instance. In most cases the value will be None, since real
    # values are merged from .json files (foo.auth.json; foo.env.json) onto the
    # settings instance during application initialization.
    SETTINGS = {}

    @classmethod
    def merge_onto(cls, settings):
        """Merge class-level settings onto a django `settings` module."""
        for key, value in cls.SETTINGS.iteritems():
            setattr(settings, key, value)


class GoogleOauth2(BaseProvider):
    """Provider for Google's Oauth2 auth system."""

    AUTHENTICATION_BACKEND = 'social.backends.google.GoogleOAuth2'
    NAME = 'Google'
    SETTINGS = {
        'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY': None,
        'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET': None,
    }


class LinkedInOauth2(BaseProvider):
    """Provider for LinkedIn's Oauth2 auth system."""

    AUTHENTICATION_BACKEND = 'social.backends.linkedin.LinkedinOAuth2'
    NAME = 'LinkedIn'
    SETTINGS = {
        'SOCIAL_AUTH_LINKEDIN_OAUTH2_KEY': None,
        'SOCIAL_AUTH_LINKEDIN_OAUTH2_SECRET': None,
    }


class MozillaPersona(BaseProvider):
    """Provider for Mozilla's Persona auth system."""

    AUTHENTICATION_BACKEND = 'social.backends.persona.PersonaAuth'
    NAME = 'Mozilla Persona'


class Registry(object):
    """Singleton registry of third-party auth providers.

    Providers must subclass BaseProvider in order to be usable in the registry.
    """

    _CONFIGURED = False
    _ENABLED = {}

    @classmethod
    def _check_configured(cls):
        """Ensures registry is configured."""
        if not cls._CONFIGURED:
            raise RuntimeError('Registry not configured')

    @classmethod
    def _get_all(cls):
        """Gets all provider implementations loaded into the Python runtime."""
        # BaseProvider does so have __subclassess__. pylint: disable-msg=no-member
        return {klass.NAME: klass for klass in BaseProvider.__subclasses__()}

    @classmethod
    def _enable(cls, provider):
        """Enables a single `provider`."""
        if provider.NAME in cls._ENABLED:
            raise ValueError('Provider %s already enabled' % provider.NAME)
        cls._ENABLED[provider.NAME] = provider

    @classmethod
    def configure_once(cls, provider_names):
        """Configures providers.

        Takes `provider_names`, a list of string.
        """
        if cls._CONFIGURED:
            raise ValueError('Provider registry already configured')
        # Flip the bit eagerly -- configure() should not be re-callable if one
        # _enable call fails.
        cls._CONFIGURED = True
        for name in provider_names:
            all_providers = cls._get_all()
            if name not in all_providers:
                raise ValueError('No implementation found for provider ' + name)
            cls._enable(all_providers.get(name))

    @classmethod
    def enabled(cls):
        """Returns list of enabled providers."""
        cls._check_configured()
        return sorted(cls._ENABLED.values(), key=lambda provider: provider.NAME)

    @classmethod
    def get(cls, provider_name):
        """Gets provider named `provider_name` string if enabled, else None."""
        cls._check_configured()
        return cls._ENABLED.get(provider_name)

    @classmethod
    def _reset(cls):
        """Returns the registry to an unconfigured state; for tests only."""
        cls._CONFIGURED = False
        cls._ENABLED = {}
