"""Third-party auth provider definitions.

Loaded by Django's settings mechanism. Consequently, this module must not
invoke the Django armature.
"""

from social.backends import google, linkedin, facebook

_DEFAULT_ICON_CLASS = 'icon-signin'


class BaseProvider(object):
    """Abstract base class for third-party auth providers.

    All providers must subclass BaseProvider -- otherwise, they cannot be put
    in the provider Registry.
    """

    # Class. The provider's backing social.backends.base.BaseAuth child.
    BACKEND_CLASS = None
    # String. Name of the FontAwesome glyph to use for sign in buttons (or the
    # name of a user-supplied custom glyph that is present at runtime).
    ICON_CLASS = _DEFAULT_ICON_CLASS
    # String. User-facing name of the provider. Must be unique across all
    # enabled providers. Will be presented in the UI.
    NAME = None
    # Dict of string -> object. Settings that will be merged into Django's
    # settings instance. In most cases the value will be None, since real
    # values are merged from .json files (foo.auth.json; foo.env.json) onto the
    # settings instance during application initialization.
    SETTINGS = {}

    @classmethod
    def get_authentication_backend(cls):
        """Gets associated Django settings.AUTHENTICATION_BACKEND string."""
        return '%s.%s' % (cls.BACKEND_CLASS.__module__, cls.BACKEND_CLASS.__name__)

    @classmethod
    def get_email(cls, unused_provider_details):
        """Gets user's email address.

        Provider responses can contain arbitrary data. This method can be
        overridden to extract an email address from the provider details
        extracted by the social_details pipeline step.

        Args:
            unused_provider_details: dict of string -> string. Data about the
                user passed back by the provider.

        Returns:
            String or None. The user's email address, if any.
        """
        return None

    @classmethod
    def get_name(cls, unused_provider_details):
        """Gets user's name.

        Provider responses can contain arbitrary data. This method can be
        overridden to extract a full name for a user from the provider details
        extracted by the social_details pipeline step.

        Args:
            unused_provider_details: dict of string -> string. Data about the
                user passed back by the provider.

        Returns:
            String or None. The user's full name, if any.
        """
        return None

    @classmethod
    def get_register_form_data(cls, pipeline_kwargs):
        """Gets dict of data to display on the register form.

        common.djangoapps.student.views.register_user uses this to populate the
        new account creation form with values supplied by the user's chosen
        provider, preventing duplicate data entry.

        Args:
            pipeline_kwargs: dict of string -> object. Keyword arguments
                accumulated by the pipeline thus far.

        Returns:
            Dict of string -> string. Keys are names of form fields; values are
            values for that field. Where there is no value, the empty string
            must be used.
        """
        # Details about the user sent back from the provider.
        details = pipeline_kwargs.get('details')

        # Get the username separately to take advantage of the de-duping logic
        # built into the pipeline. The provider cannot de-dupe because it can't
        # check the state of taken usernames in our system. Note that there is
        # technically a data race between the creation of this value and the
        # creation of the user object, so it is still possible for users to get
        # an error on submit.
        suggested_username = pipeline_kwargs.get('username')

        return {
            'email': cls.get_email(details) or '',
            'name': cls.get_name(details) or '',
            'username': suggested_username,
        }

    @classmethod
    def merge_onto(cls, settings):
        """Merge class-level settings onto a django settings module."""
        for key, value in cls.SETTINGS.iteritems():
            setattr(settings, key, value)


class GoogleOauth2(BaseProvider):
    """Provider for Google's Oauth2 auth system."""

    BACKEND_CLASS = google.GoogleOAuth2
    ICON_CLASS = 'icon-google-plus'
    NAME = 'Google'
    SETTINGS = {
        'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY': None,
        'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET': None,
    }

    @classmethod
    def get_email(cls, provider_details):
        return provider_details.get('email')

    @classmethod
    def get_name(cls, provider_details):
        return provider_details.get('fullname')


class LinkedInOauth2(BaseProvider):
    """Provider for LinkedIn's Oauth2 auth system."""

    BACKEND_CLASS = linkedin.LinkedinOAuth2
    ICON_CLASS = 'icon-linkedin'
    NAME = 'LinkedIn'
    SETTINGS = {
        'SOCIAL_AUTH_LINKEDIN_OAUTH2_KEY': None,
        'SOCIAL_AUTH_LINKEDIN_OAUTH2_SECRET': None,
    }

    @classmethod
    def get_email(cls, provider_details):
        return provider_details.get('email')

    @classmethod
    def get_name(cls, provider_details):
        return provider_details.get('fullname')


class FacebookOauth2(BaseProvider):
    """Provider for LinkedIn's Oauth2 auth system."""

    BACKEND_CLASS = facebook.FacebookOAuth2
    ICON_CLASS = 'icon-facebook'
    NAME = 'Facebook'
    SETTINGS = {
        'SOCIAL_AUTH_FACEBOOK_KEY': None,
        'SOCIAL_AUTH_FACEBOOK_SECRET': None,
    }

    @classmethod
    def get_email(cls, provider_details):
        return provider_details.get('email')

    @classmethod
    def get_name(cls, provider_details):
        return provider_details.get('fullname')


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
        """Enables a single provider."""
        if provider.NAME in cls._ENABLED:
            raise ValueError('Provider %s already enabled' % provider.NAME)
        cls._ENABLED[provider.NAME] = provider

    @classmethod
    def configure_once(cls, provider_names):
        """Configures providers.

        Args:
            provider_names: list of string. The providers to configure.

        Raises:
            ValueError: if the registry has already been configured, or if any
            of the passed provider_names does not have a corresponding
            BaseProvider child implementation.
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
        """Gets provider named provider_name string if enabled, else None."""
        cls._check_configured()
        return cls._ENABLED.get(provider_name)

    @classmethod
    def get_by_backend_name(cls, backend_name):
        """Gets provider (or None) by backend name.

        Args:
            backend_name: string. The python-social-auth
                backends.base.BaseAuth.name (for example, 'google-oauth2') to
                try and get a provider for.

        Raises:
            RuntimeError: if the registry has not been configured.
        """
        cls._check_configured()
        for enabled in cls._ENABLED.values():
            if enabled.BACKEND_CLASS.name == backend_name:
                return enabled

    @classmethod
    def _reset(cls):
        """Returns the registry to an unconfigured state; for tests only."""
        cls._CONFIGURED = False
        cls._ENABLED = {}
