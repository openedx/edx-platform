"""Settings for the third-party auth module.

Defers configuration of settings so we can inspect the provider registry and
create settings placeholders for only those values actually needed by a given
deployment. Required by Django; consequently, this file must not invoke the
Django armature.

The flow for settings registration is:

The base settings file contains a boolean, ENABLE_THIRD_PARTY_AUTH, indicating
whether this module is enabled. Ancillary settings files (aws.py, dev.py) put
options in THIRD_PARTY_SETTINGS. startup.py probes the ENABLE_THIRD_PARTY_AUTH.
If true, it:

    a) loads this module.
    b) calls apply_settings(), passing in settings.THIRD_PARTY_AUTH.
       THIRD_PARTY AUTH is a dict of the form

       'THIRD_PARTY_AUTH': {
            '<PROVIDER_NAME>': {
                '<PROVIDER_SETTING_NAME>': '<PROVIDER_SETTING_VALUE>',
                [...]
            },
            [...]
       }

       If you are using a dev settings file, your settings dict starts at the
       level of <PROVIDER_NAME> and is a map of provider name string to
       settings dict. If you are using an auth.json file, it should contain a
       THIRD_PARTY_AUTH entry as above.
    c) apply_settings() builds a list of <PROVIDER_NAMES>. These are the
       enabled third party auth providers for the deployment. These are enabled
       in provider.Registry, the canonical list of enabled providers.
    d) then, it sets global, provider-independent settings.
    e) then, it sets provider-specific settings. For each enabled provider, we
       read its SETTINGS member. These are merged onto the Django settings
       object. In most cases these are stubs and the real values are set from
       THIRD_PARTY_AUTH. All values that are set from this dict must first be
       initialized from SETTINGS. This allows us to validate the dict and
       ensure that the values match expected configuration options on the
       provider.
    f) finally, the (key, value) pairs from the dict file are merged onto the
       django settings object.
"""

from . import provider


_FIELDS_STORED_IN_SESSION = ['auth_entry']
_MIDDLEWARE_CLASSES = (
    'third_party_auth.middleware.ExceptionMiddleware',
)
_SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/dashboard'


def _merge_auth_info(django_settings, auth_info):
    """Merge auth_info dict onto django_settings module."""
    enabled_provider_names = []
    to_merge = []

    for provider_name, provider_dict in auth_info.items():
        enabled_provider_names.append(provider_name)
        # Merge iff all settings have been intialized.
        for key in provider_dict:
            if key not in dir(django_settings):
                raise ValueError('Auth setting %s not initialized' % key)
        to_merge.append(provider_dict)

    for passed_validation in to_merge:
        for key, value in passed_validation.iteritems():
            setattr(django_settings, key, value)


def _set_global_settings(django_settings):
    """Set provider-independent settings."""

    # Whitelisted URL query parameters retrained in the pipeline session.
    # Params not in this whitelist will be silently dropped.
    django_settings.FIELDS_STORED_IN_SESSION = _FIELDS_STORED_IN_SESSION

    # Register and configure python-social-auth with Django.
    django_settings.INSTALLED_APPS += (
        'social.apps.django_app.default',
        'third_party_auth',
    )

    # Inject exception middleware to make redirects fire.
    django_settings.MIDDLEWARE_CLASSES += _MIDDLEWARE_CLASSES

    # Where to send the user if there's an error during social authentication
    # and we cannot send them to a more specific URL
    # (see middleware.ExceptionMiddleware).
    django_settings.SOCIAL_AUTH_LOGIN_ERROR_URL = '/'

    # Where to send the user once social authentication is successful.
    django_settings.SOCIAL_AUTH_LOGIN_REDIRECT_URL = _SOCIAL_AUTH_LOGIN_REDIRECT_URL

    # Inject our customized auth pipeline. All auth backends must work with
    # this pipeline.
    django_settings.SOCIAL_AUTH_PIPELINE = (
        'third_party_auth.pipeline.parse_query_params',
        'social.pipeline.social_auth.social_details',
        'social.pipeline.social_auth.social_uid',
        'social.pipeline.social_auth.auth_allowed',
        'social.pipeline.social_auth.social_user',
        'social.pipeline.user.get_username',
        'third_party_auth.pipeline.redirect_to_supplementary_form',
        'social.pipeline.user.create_user',
        'social.pipeline.social_auth.associate_user',
        'social.pipeline.social_auth.load_extra_data',
        'social.pipeline.user.user_details',
        'third_party_auth.pipeline.login_analytics',
    )

    # We let the user specify their email address during signup.
    django_settings.SOCIAL_AUTH_PROTECTED_USER_FIELDS = ['email']

    # Disable exceptions by default for prod so you get redirect behavior
    # instead of a Django error page. During development you may want to
    # enable this when you want to get stack traces rather than redirections.
    django_settings.SOCIAL_AUTH_RAISE_EXCEPTIONS = False

    # Context processors required under Django.
    django_settings.SOCIAL_AUTH_UUID_LENGTH = 4
    django_settings.TEMPLATE_CONTEXT_PROCESSORS += (
        'social.apps.django_app.context_processors.backends',
        'social.apps.django_app.context_processors.login_redirect',
    )


def _set_provider_settings(django_settings, enabled_providers, auth_info):
    """Sets provider-specific settings."""
    # Must prepend here so we get called first.
    django_settings.AUTHENTICATION_BACKENDS = (
        tuple(enabled_provider.get_authentication_backend() for enabled_provider in enabled_providers) +
        django_settings.AUTHENTICATION_BACKENDS)

    # Merge settings from provider classes, and configure all placeholders.
    for enabled_provider in enabled_providers:
        enabled_provider.merge_onto(django_settings)

    # Merge settings from <deployment>.auth.json, overwriting placeholders.
    _merge_auth_info(django_settings, auth_info)


def apply_settings(auth_info, django_settings):
    """Applies settings from auth_info dict to django_settings module."""
    provider_names = auth_info.keys()
    provider.Registry.configure_once(provider_names)
    enabled_providers = provider.Registry.enabled()
    _set_global_settings(django_settings)
    _set_provider_settings(django_settings, enabled_providers, auth_info)
