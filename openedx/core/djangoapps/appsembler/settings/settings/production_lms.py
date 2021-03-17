"""
Settings for Appsembler on LMS in Production.
"""
from os import path

from openedx.core.djangoapps.appsembler.settings.settings import production_common


EDX_SITE_REDIRECT_MIDDLEWARE = "django_sites_extensions.middleware.RedirectMiddleware"
TAHOE_MARKETING_SITE_URL = "https://appsembler.com/tahoe"


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
    settings.MIDDLEWARE += [
        # LmsCurrentOrganizationMiddleware needs to go before `TiersMiddleware` in aws_common.plugin_settings()
        'openedx.core.djangoapps.appsembler.sites.middleware.LmsCurrentOrganizationMiddleware',
    ]

    production_common.plugin_settings(settings)

    if settings.APPSEMBLER_FEATURES.get("TAHOE_ENABLE_DOMAIN_REDIRECT_MIDDLEWARE", True):
        redir_middleware_index = settings.MIDDLEWARE.index(EDX_SITE_REDIRECT_MIDDLEWARE)
        settings.MIDDLEWARE.insert(
            redir_middleware_index,  # Insert after Django RedirectMiddleware
            'openedx.core.djangoapps.appsembler.sites.middleware.CustomDomainsRedirectMiddleware'
        )
        settings.MIDDLEWARE.insert(
            redir_middleware_index + 1,  # Insert after CustomDomainsRedirectMiddleware
            'openedx.core.djangoapps.appsembler.sites.middleware.RedirectMiddleware'
        )

        settings.TAHOE_MAIN_SITE_REDIRECT_URL = settings.ENV_TOKENS.get(
            'TAHOE_MAIN_SITE_REDIRECT_URL', TAHOE_MARKETING_SITE_URL
        )
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

    if settings.FEATURES.get('TAHOE_YEARLY_AMC_TOKENS', True):
        # TODO: RED-1901 Remove this feature and reduce the time back to one hour.
        #       Extending AMC tokens from an hour to a year is _not_ a good idea but needed for AMC to work and
        #       maintain pre-Juniper behaviour. This should be refactored to improve AMC token and refresh flow.
        total_seconds_in_year = 365 * 24 * 3600
        settings.OAUTH2_PROVIDER['REFRESH_TOKEN_EXPIRE_SECONDS'] = total_seconds_in_year
        settings.OAUTH2_PROVIDER['ACCESS_TOKEN_EXPIRE_SECONDS'] = total_seconds_in_year

    if settings.SENTRY_DSN:
        settings.RAVEN_CONFIG['tags']['app'] = 'lms'

    settings.ACCESS_CONTROL_BACKENDS = settings.ENV_TOKENS.get('ACCESS_CONTROL_BACKENDS', {})
    settings.LMS_SEGMENT_SITE = settings.AUTH_TOKENS.get('SEGMENT_SITE')

    _add_theme_static_dirs(settings)
