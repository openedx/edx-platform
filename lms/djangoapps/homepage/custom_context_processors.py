"""
All custom made context processors for Homepage app
"""
from edx_notifications.server.web.utils import get_notifications_widget_context

from .constants import CONFIGS


def notifications_configs(request):  # pylint: disable=unused-argument
    """
    Context processor to set global configs for edx-notifications
    :param request:
    :return: edx-notifications global configs
    """

    return get_notifications_widget_context(CONFIGS)
