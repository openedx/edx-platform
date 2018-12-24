"""
Settings for Appsembler on devstack/LMS.
"""

from openedx.core.djangoapps.appsembler.settings.settings import devstack_common


def plugin_settings(settings):
    """
    Make devstack lookin shiny blue!
    """
    devstack_common.plugin_settings(settings)

    settings.INSTALLED_APPS += (
        'openedx.core.djangoapps.appsembler.tpa_admin',
    )

    settings.CORS_ORIGIN_ALLOW_ALL = True

    settings.CORS_ALLOW_HEADERS = (
        'x-requested-with',
        'content-type',
        'accept',
        'origin',
        'authorization',
        'x-csrftoken',
        'cache-control'
    )
    settings.DEBUG_TOOLBAR_PATCH_SETTINGS = False

    # settings.SITE_ID = 1

    # TODO: Fix the error and enable the Tahoe backends
    # settings.AUTHENTICATION_BACKENDS = (
    #     'organizations.backends.DefaultSiteBackend',
    #     'organizations.backends.SiteMemberBackend',
    #     'organizations.backends.OrganizationMemberBackend',
    # )

    settings.EDX_API_KEY = "test"

    settings.COURSE_CATALOG_VISIBILITY_PERMISSION = 'see_in_catalog'
    settings.COURSE_ABOUT_VISIBILITY_PERMISSION = 'see_about_page'
    settings.SEARCH_SKIP_ENROLLMENT_START_DATE_FILTERING = True

    settings.ALTERNATE_QUEUE_ENVS = ['cms']

    settings.USE_S3_FOR_CUSTOMER_THEMES = False

    settings.LMS_BASE = settings.ENV_TOKENS.get('LMS_BASE')

    if settings.FEATURES.get('ENABLE_THIRD_PARTY_AUTH'):
        settings.AUTHENTICATION_BACKENDS = list(settings.AUTHENTICATION_BACKENDS) + (
            settings.ENV_TOKENS.get('THIRD_PARTY_AUTH_BACKENDS', [
                'social_core.backends.google.GoogleOAuth2',
                'social_core.backends.linkedin.LinkedinOAuth2',
                'social_core.backends.facebook.FacebookOAuth2',
                'social_core.backends.azuread.AzureADOAuth2',
                'third_party_auth.saml.SAMLAuthBackend',
                'third_party_auth.lti.LTIAuthBackend',
            ])
        )
