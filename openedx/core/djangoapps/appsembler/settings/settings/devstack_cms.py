"""
Settings for Appsembler on devstack/CMS.
"""

from openedx.core.djangoapps.appsembler.settings.settings import devstack_common


def plugin_settings(settings):
    """
    Make devstack lookin shiny blue!
    """
    devstack_common.plugin_settings(settings)

    settings.XQUEUE_WAITTIME_BETWEEN_REQUESTS = 5

    settings.ALTERNATE_QUEUE_ENVS = ['lms']
