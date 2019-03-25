"""
Settings for Appsembler on devstack/CMS.
"""

from openedx.core.djangoapps.appsembler.settings.settings import devstack_common


def plugin_settings(settings):
    """
    Appsembler CMS overrides for devstack.
    """
    devstack_common.plugin_settings(settings)

    settings.ALTERNATE_QUEUE_ENVS = ['lms']
