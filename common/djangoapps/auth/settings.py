"""Settings for the third-party auth module.

Defers configuration of settings so we can inspect the provider registry and create settings placeholders for only those
values actually needed by a given deployment. Required by Django; consequently, this file must not invoke the Django
armature.

The flow for settings registration is:

The base settings file contains a boolean, ENABLE_THIRD_PARTY_AUTH, indicating whether the auth module is enabled.
The environment's (cms/lms) aws.py settings file probes the boolean. If true, it:

    a) loads the auth module.
    b) loads the AUTH object from the <environment>.auth.json. The auth object is of the form

       'AUTH': {
            '<PROVIDER_NAME>': {
                '<PROVIDER_SETTING_NAME>': '<PROVIDER_SETTING_VALUE>',
                [...]
            },
            [...]
       }

    c) builds the list of <PROVIDER_NAMES>. These are the enabled third party auth providers for the deployment. These
       are enabled in provider.Registry, the canonical list of enabled providers.
    d) sets global, provider-independent settings.
    e) sets provider-specific settings. For each enabled provider, we then read its SETTINGS. These are merged onto the
       Django settings object. In most cases these are stubs and the real values are set by <environment>.auth.json. All
       values that are set from the json file must first be initialized from SETTINGS. This allows us to validate the
       json file and ensure that the values match expected configuration options on the provider.
    f) finally, the (key, value) pairs from the json file are merged onto the django settings object.
"""

from . import provider


def _merge_auth_info(django_settings, auth_info):
    """Merge `auth_info` dict onto `django_settings` dict."""
    enabled_provider_names = []
    to_merge = []

    for provider_name, provider_dict in auth_info.items():
        enabled_provider_names.append(provider_name)
        # Merge iff all settings have been intialized.
        for key in provider_dict:
            if key not in django_settings:
                raise ValueError('Auth setting %s not initialized' % key)
        to_merge.append(provider_dict)

    for passed_validation in to_merge:
        django_settings.update(passed_validation)


def _set_global_settings(django_settings):
    """Set provider-independent settings."""
    # Register and configure python-social-auth with Django.
    django_settings['INSTALLED_APPS'] += (
        'social.apps.django_app.default',
    )
    django_settings['TEMPLATE_CONTEXT_PROCESSORS'] += (
        'social.apps.django_app.context_processors.backends',
        'social.apps.django_app.context_processors.login_redirect',
    )
    # Inject our customized auth pipeline. All auth backends must work with this pipeline.
    django_settings['SOCIAL_AUTH_PIPELINE'] = (
        'auth.pipeline.step',
    )


def _set_provider_settings(django_settings, enabled_providers, auth_info):
    """Set provider-specific settings."""
    django_settings['AUTHENTICATION_BACKENDS'] = tuple(
        enabled_provider.AUTHENTICATION_BACKEND for enabled_provider in enabled_providers) + \
        django_settings['AUTHENTICATION_BACKENDS']

    # Merge settings from provider classes, and configure all placeholders.
    for enabled_provider in enabled_providers:
        enabled_provider.merge_onto(django_settings)

    # Merge settings from <deployment>.auth.json.
    _merge_auth_info(django_settings, auth_info)


def patch(auth_info, django_settings):
    """Patch `auth_info` dict onto `django_settings` dict."""
    provider_names = auth_info.keys()
    provider.Registry.configure_once(provider_names)
    enabled_providers = provider.Registry.enabled()
    _set_global_settings(django_settings)
    _set_provider_settings(django_settings, enabled_providers, auth_info)
