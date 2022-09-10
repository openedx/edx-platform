"""Common environment variables unique to the discussion plugin."""


def plugin_settings(settings):
    """Settings for the discussions plugin. """
    # .. toggle_name: ALLOW_HIDING_DISCUSSION_TAB
    # .. toggle_implementation: DjangoSetting
    # .. toggle_default: False
    # .. toggle_description: If True, it adds an option to show/hide the discussions tab.
    # .. toggle_use_cases: open_edx
    # .. toggle_creation_date: 2015-06-15
    # .. toggle_tickets: https://github.com/openedx/edx-platform/pull/8474
    settings.FEATURES['ALLOW_HIDING_DISCUSSION_TAB'] = False
    settings.DISCUSSION_SETTINGS = {
        'MAX_COMMENT_DEPTH': 2,
        'COURSE_PUBLISH_TASK_DELAY': 30,
    }
