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

    settings.USE_S3_FOR_CUSTOMER_THEMES = False
    if settings.ENABLE_COMPREHENSIVE_THEMING:
        assert len(settings.COMPREHENSIVE_THEME_DIRS) == 1, (
            'Tahoe supports a single theme, please double check that '
            'you have only one directory in the `COMPREHENSIVE_THEME_DIRS` setting.'
        )

        # Add the LMS-generated customer CSS files to the list
        # LMS-generated files looks like: `appsembler-academy.tahoe.appsembler.com.css`
        customer_themes_dir = path.join(settings.COMPREHENSIVE_THEME_DIRS[0], 'customer_themes')
        if path.isdir(customer_themes_dir):
            settings.STATICFILES_DIRS.insert(0, ('customer_themes', customer_themes_dir))

    # This is used in the appsembler_sites.middleware.RedirectMiddleware to exclude certain paths
    # from the redirect mechanics.
    if settings.APPSEMBLER_FEATURES.get("TAHOE_ENABLE_DOMAIN_REDIRECT_MIDDLEWARE", True):
        settings.MAIN_SITE_REDIRECT_WHITELIST += ['/media/']
