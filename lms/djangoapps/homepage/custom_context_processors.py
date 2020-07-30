from edx_notifications.server.web.utils import get_notifications_widget_context

from .constants import CONFIGS


def notifications_context(request):
    """
    Context processor to set global context for edx-notifications
    :param request:
    :return: edx-notifications global context
    """

    return get_notifications_widget_context(CONFIGS)
