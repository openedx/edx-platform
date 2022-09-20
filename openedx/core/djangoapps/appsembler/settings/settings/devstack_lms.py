"""
Settings for Appsembler on devstack/LMS.
"""
from os import path

from openedx.core.djangoapps.appsembler.settings.settings import devstack_common


def plugin_settings(settings):
    """
    Appsembler LMS overrides for devstack.
    """
    devstack_common.plugin_settings(settings)

    settings.DEBUG_TOOLBAR_PATCH_SETTINGS = False

    settings.SITE_ID = 1

    settings.EDX_API_KEY = "test"

    settings.ALTERNATE_QUEUE_ENVS = ['cms']

    if settings.ENABLE_COMPREHENSIVE_THEMING:
        assert len(settings.COMPREHENSIVE_THEME_DIRS), (
            'Tahoe supports a single theme, please double check that '
            'you have only one directory in the `COMPREHENSIVE_THEME_DIRS` setting.'
        )

    # This is used in the appsembler_sites.middleware.RedirectMiddleware to exclude certain paths
    # from the redirect mechanics.
    if settings.APPSEMBLER_FEATURES.get("TAHOE_ENABLE_DOMAIN_REDIRECT_MIDDLEWARE", True):
        settings.MAIN_SITE_REDIRECT_ALLOWLIST += ['/media/']
