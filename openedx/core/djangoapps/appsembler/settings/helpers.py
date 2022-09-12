"""
Helpers for the settings.
"""

from os import path


def get_tahoe_theme_static_dirs(settings):
    """
    Get STATICFILES_DIRS for Tahoe to enable Appsembler Themes static files customizations.

    :param settings (Django settings module).
    :return STATICFILES_DIRS for Tahoe.
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
        static_files_dir_setting = settings.STATICFILES_DIRS
        if path.isdir(theme_static):
            static_files_dir_setting += [theme_static]
        return static_files_dir_setting
    # comprehensive theming not enabled
    return settings.STATICFILES_DIRS


def get_tahoe_multitenant_auth_backends(settings):
    """
    Support Multi-Tenancy via OrganizationMemberBackend and DefaultSiteBackend instead of the edX's backend.

    :param settings (Django settings module).
    :return AUTHENTICATION_BACKENDS for Tahoe.

    Release upgrade note: This function modifies the AUTHENTICATION_BACKENDS by removing unwanted backends and adding
                          Tahoe-needed multi-tenant backends. Without this function Tahoe won't function properly
                          and there will be either silently missing features such as hidden Instructor
                          Dashboard (RED-1924) or silently breaking Tahoe security.
    """

    upstream_user_model_backend = \
        'openedx.core.djangoapps.oauth_dispatch.dot_overrides.backends.EdxRateLimitedAllowAllUsersModelBackend'

    if upstream_user_model_backend not in settings.AUTHENTICATION_BACKENDS:
        # EdxRateLimitedAllowAllUsersModelBackend is missing from the settings.
        # It helps to compare AUTHENTICATION_BACKENDS before and after this exception was raised.
        raise Exception(
            'Tahoe Security: settings.AUTHENTICATION_BACKENDS have changes by either upstream release upgrade or a '
            'configuration change. '
            'This means that the `use_tahoe_multitenant_auth_backends` function should be updated accordingly. '
            'While there is no clear path to address this change, it is safer to avoid breaking authentication '
            'silently.'
        )

    authentication_backends = settings.AUTHENTICATION_BACKENDS

    if settings.APPSEMBLER_FEATURES.get('ENABLE_APPSEMBLER_AUTH_BACKENDS', True):
        upstream_backend_index = authentication_backends.index(upstream_user_model_backend)

        # Use multi-tenant Tahoe backends instead of the upstream EdxRateLimitedAllowAllUsersModelBackend backend.
        authentication_backends = settings.AUTHENTICATION_BACKENDS[:upstream_backend_index] + [
            'tahoe_sites.backends.DefaultSiteBackend',
            'tahoe_sites.backends.OrganizationMemberBackend',
        ] + settings.AUTHENTICATION_BACKENDS[upstream_backend_index + 1:]

    return authentication_backends
