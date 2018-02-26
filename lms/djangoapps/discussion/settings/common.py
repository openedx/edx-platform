"""Common environment variables unique to the discussion plugin."""


def plugin_settings(settings):
    """Settings for the discussions plugin. """
    settings.FEATURES['ALLOW_HIDING_DISCUSSION_TAB'] = False
