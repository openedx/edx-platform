"""Third-party auth provider definitions.

Loaded by Django's settings mechanism. Consequently, this module must not invoke the Django armature.
"""


class BaseProvider(object):

    # String. Dot-delimited module.Class. The name of the backend implementation to load. 
    AUTHENTICATION_BACKEND = None
    # String. User-facing name of the provider. Must be unique across all enabled providers.
    NAME = None


class GoogleOauth2(BaseProvider):

    AUTHENTICATION_BACKEND = 'social.backends.google.GoogleOAuth2'
    NAME = 'Google'


class MozillaPersona(BaseProvider):

    AUTHENTICATION_BACKEND = 'social.backends.persona.PersonaAuth'
    NAME = 'Mozilla Persona'


class Registry(object):
    """Singleton registry of third-party auth providers."""

    _ALL = {klass.NAME: klass for klass in BaseProvider.__subclasses__()}
    _CONFIGURED = False
    _ENABLED = {}

    @classmethod
    def _enable(cls, provider):
        if provider.NAME in cls._ENABLED:
            raise ValueError('Provider %s already enabled' % provider.NAME)
        cls._ENABLED[provider.NAME] = provider

    @classmethod
    def configure_once(cls, provider_names):
        """Configures providers; takes `provider_names`, a list of string, and enables them."""
        if cls._CONFIGURED:
            raise ValueError('Provider registry already configured')
        # Flip the bit eagerly -- configure() should not be re-callable if one _enable call fails.
        cls._CONFIGURED = True
        for name in provider_names:
            if name not in cls._ALL:
                raise ValueError('No implementation found for provider ' + name)
            cls._enable(cls._ALL.get(name))

    @classmethod
    def enabled(cls):
        """Returns list of enabled providers."""
        return sorted(cls._ENABLED.values(), key=lambda provider: provider.NAME)

    @classmethod
    def get(cls, provider_name):
        """Returns provider matching `provider_name` string if provider is enabled, else None."""
        return cls._ENABLED.get(provider_name)

    @classmethod
    def _reset(cls):
        cls._CONFIGURED = False
        cls._ENABLED = {}
