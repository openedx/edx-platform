"""
Settings for Appsembler on devstack/LMS.
"""

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
