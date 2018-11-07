"""Common environment variables unique to the discussion plugin."""


def plugin_settings(settings):
    """Settings for the discussions plugin. """
    settings.FEATURES['ALLOW_HIDING_DISCUSSION_TAB'] = False
    settings.DISCUSSION_SETTINGS = {
        'MAX_COMMENT_DEPTH': 2,
        'COURSE_PUBLISH_TASK_DELAY': 30,
    }
