"""
Settings for Appsembler on LMS in Production (aka AWS).
"""

from openedx.core.djangoapps.appsembler.settings.settings import aws_common


def plugin_settings(settings):
    """
    Appsembler LMS overrides for both production AND devstack.

    Make sure those are compatible for devstack via defensive coding.

    This file, however, won't run in test environments.
    """
    aws_common.plugin_settings(settings)

    settings.LMS_BASE = settings.ENV_TOKENS.get('LMS_BASE')

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

    settings.SEARCH_INITIALIZER = "lms.lib.courseware_search.lms_search_initializer.LmsSearchInitializer"
    settings.SEARCH_RESULT_PROCESSOR = "lms.lib.courseware_search.lms_result_processor.LmsSearchResultProcessor"
    settings.SEARCH_FILTER_GENERATOR = "lms.lib.courseware_search.lms_filter_generator.LmsSearchFilterGenerator"

    # enable course visibility feature flags
    settings.COURSE_CATALOG_VISIBILITY_PERMISSION = 'see_in_catalog'
    settings.COURSE_ABOUT_VISIBILITY_PERMISSION = 'see_about_page'
    settings.SEARCH_SKIP_ENROLLMENT_START_DATE_FILTERING = True

    if settings.APPSEMBLER_FEATURES.get('ENABLE_APPSEMBLER_AUTH_BACKENDS', True):
        settings.AUTHENTICATION_BACKENDS = (
            'organizations.backends.DefaultSiteBackend',
            'organizations.backends.SiteMemberBackend',
            'organizations.backends.OrganizationMemberBackend',
        )

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

    if settings.SENTRY_DSN:
        settings.RAVEN_CONFIG['tags']['app'] = 'lms'

    # This is used in the appsembler_sites.middleware.RedirectMiddleware to exclude certain paths
    # from the redirect mechanics.
    settings.MAIN_SITE_REDIRECT_WHITELIST = ['api', 'admin', 'oauth', 'status']

    settings.USE_S3_FOR_CUSTOMER_THEMES = True
