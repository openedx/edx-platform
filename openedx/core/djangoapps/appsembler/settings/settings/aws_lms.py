"""
Settings for Appsembler on LMS in Production (aka AWS).
"""
from os import path

from openedx.core.djangoapps.appsembler.settings.settings import aws_common


EDX_SITE_REDIRECT_MIDDLEWARE = "django_sites_extensions.middleware.RedirectMiddleware"


def _add_theme_static_dirs(settings):
    """
    Appsembler Themes static files customizations.
    """
    from openedx.core.djangoapps.theming.helpers_dirs import (
        get_themes_unchecked,
        get_theme_base_dirs_from_settings
    )

    if settings.ENABLE_COMPREHENSIVE_THEMING:
        themes_dirs = get_theme_base_dirs_from_settings(settings.COMPREHENSIVE_THEME_DIRS)
        themes = get_themes_unchecked(themes_dirs, settings.PROJECT_ROOT)

        assert len(themes), 'Customer themes enabled, but it seems that there is no Tahoe theme.'
        assert len(themes) == 1, (
            'Customer themes enabled, but it looks like there is more than one theme, '
            'however Tahoe does only supports having a single instance of `edx-theme-codebase`'
            'and no other theme should be installed.'
        )

        theme = themes[0]

        # Allow the theme to override the platform files transparently
        # without having to change the Open edX code.
        theme_static = theme.path / 'static'
        if path.isdir(theme_static):
            settings.STATICFILES_DIRS.append(theme_static)


def plugin_settings(settings):
    """
    Appsembler LMS overrides for both production AND devstack.

    Make sure those are compatible for devstack via defensive coding.

    This file, however, won't run in test environments.
    """
    settings.MIDDLEWARE_CLASSES += (
        # LmsCurrentOrganizationMiddleware needs to go before `TiersMiddleware` in aws_common.plugin_settings()
        'openedx.core.djangoapps.appsembler.sites.middleware.LmsCurrentOrganizationMiddleware',
    )

    aws_common.plugin_settings(settings)

    if settings.APPSEMBLER_FEATURES.get("TAHOE_ENABLE_DOMAIN_REDIRECT_MIDDLEWARE", True):
        redir_middleware = settings.MIDDLEWARE_CLASSES.index(EDX_SITE_REDIRECT_MIDDLEWARE)
        for tahoe_redir_middleware in (
            'openedx.core.djangoapps.appsembler.sites.middleware.CustomDomainsRedirectMiddleware',
            'openedx.core.djangoapps.appsembler.sites.middleware.RedirectMiddleware'
        ):
            settings.MIDDLEWARE_CLASSES.insert(redir_middleware, tahoe_redir_middleware)
        # This is used in the appsembler_sites.middleware.RedirectMiddleware to exclude certain paths
        # from the redirect mechanics.
        settings.MAIN_SITE_REDIRECT_WHITELIST = [
            'api',
            'admin',
            'oauth',
            'status',
            '/heartbeat',
            '/accounts/manage_user_standing',
            '/accounts/disable_account_ajax',
        ]

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

    settings.USE_S3_FOR_CUSTOMER_THEMES = True

    _add_theme_static_dirs(settings)
