CONFIGS = {
    'refresh_watcher': {
        'name': 'short-poll',
        'args': {
            'poll_period_secs': 5,
        }
    },
    'global_variables': {
        # we only selectively want dates in the unread
        # pane
        'always_show_dates_on_unread': False,
        'hide_link_is_visible': False,
    },
    'view_audios': {
        # no audio alert for now
        'notification_alert': None,
    },
}
