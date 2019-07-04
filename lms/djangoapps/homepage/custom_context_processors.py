from edx_notifications.server.web.utils import get_notifications_widget_context


def notifications_configs(request):
    """
        Context processor to set global configs for edx-notifications
    :param request:
    :return: edx-notifications global configs
    """
    configs = {
        "refresh_watcher": {
            "name": "short-poll",
            "args": {
                "poll_period_secs": 5,
            }
        },
        "global_variables": {
            # we only selectively want dates in the unread
            # pane
            "always_show_dates_on_unread": False,
            "hide_link_is_visible": False,
        },
        "view_audios": {
            # no audio alert for now
            "notification_alert": None,
        },
    }

    data = get_notifications_widget_context(configs)

    return data
