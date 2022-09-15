"""
Settings for Appsembler on LMS in Production.
"""

import sentry_sdk

from openedx.core.djangoapps.appsembler.settings.settings import production_common
from ..helpers import get_tahoe_theme_static_dirs, get_tahoe_multitenant_auth_backends


EDX_SITE_REDIRECT_MIDDLEWARE = "django_sites_extensions.middleware.RedirectMiddleware"
TAHOE_MARKETING_SITE_URL = "https://appsembler.com/tahoe"


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
            '/courses/yt_video_metadata',
            '/accounts/manage_user_standing',
            '/accounts/disable_account_ajax',
            '/completion-aggregator/',  # :(  no /api/ in that API path
        ]

    settings.LMS_BASE = settings.ENV_TOKENS.get('LMS_BASE')

    tpa_admin_app_name = 'openedx.core.djangoapps.appsembler.tpa_admin'
    if tpa_admin_app_name not in settings.INSTALLED_APPS:
        settings.INSTALLED_APPS += [
            tpa_admin_app_name,
        ]

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

    if settings.FEATURES.get('TAHOE_YEARLY_AMC_TOKENS', True):
        # TODO: RED-1901 Remove this feature and reduce the time back to one hour.
        #       Extending AMC tokens from an hour to a year is _not_ a good idea but needed for AMC to work and
        #       maintain pre-Juniper behaviour. This should be refactored to improve AMC token and refresh flow.
        total_seconds_in_year = 365 * 24 * 3600
        settings.OAUTH2_PROVIDER['REFRESH_TOKEN_EXPIRE_SECONDS'] = total_seconds_in_year
        settings.OAUTH2_PROVIDER['ACCESS_TOKEN_EXPIRE_SECONDS'] = total_seconds_in_year

    if settings.SENTRY_DSN:
        sentry_sdk.set_tag('app', 'lms')

    settings.ACCESS_CONTROL_BACKENDS = settings.ENV_TOKENS.get('ACCESS_CONTROL_BACKENDS', {})
    settings.LMS_SEGMENT_SITE = settings.AUTH_TOKENS.get('SEGMENT_SITE')

    settings.STATICFILES_DIRS = get_tahoe_theme_static_dirs(settings)
    settings.AUTHENTICATION_BACKENDS = get_tahoe_multitenant_auth_backends(settings)

    settings.HIJACK_LOGIN_REDIRECT_URL = '/dashboard'
