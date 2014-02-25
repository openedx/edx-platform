"""Settings for the third-party auth module.

Defers configuration of settings so we can inspect the provider registry and create settings placeholders for only those
values actually needed by a given deployment. Required by Django; consequently, this file must not invoke the Django
armature.
"""

from . import provider


def set_global_settings(settings):
    """Sets globals used by all third-party auth providers.

    Takes and mutates `settings`, the global settings dict.
    """
    # Register and configure python-social-auth with Django.
    settings['INSTALLED_APPS'] += (
        'social.apps.django_app.default',
    )
    settings['TEMPLATE_CONTEXT_PROCESSORS'] += (
        'social.apps.django_app.context_processors.backends',
        'social.apps.django_app.context_processors.login_redirect',
    )
    # Inject our customized auth pipeline. All auth backends must work with this pipeline.
    settings['SOCIAL_AUTH_PIPELINE'] = (
        'auth.pipeline.step',
    )


def set_provider_settings(settings, provider_names):
    """Sets provider-specific settings globals.

    Takes and mutates `settings`, the global settings dict; takes `provider_names`.
    """
    provider.Registry.configure(provider_names)
    provider_backends = tuple(provider.AUTHENTICATION_BACKEND for provider in provider.Registry.enabled())
    settings['AUTHENTICATION_BACKENDS'] = provider_backends + settings['AUTHENTICATION_BACKENDS']

    settings['SOCIAL_AUTH_GOOGLE_OAUTH2_KEY'] = '488331012335-6s18ou2b03lffc76bl39118ai312k9cc.apps.googleusercontent.com'
    settings['SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET'] = 'fkKU2eRWr_YO8BwHIE6L7w7g'


def patch(settings):
    set_global_settings(settings)
    set_provider_settings(settings, [provider.GoogleOauth2.NAME, provider.MozillaPersona.NAME])
