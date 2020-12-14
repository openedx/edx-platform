"""Common environment variables unique to the Course Content Bookmarks plugin."""


def plugin_settings(settings):
    """Settings for the Course Content Bookmarks plugin. """
    settings.MAX_BOOKMARKS_PER_COURSE = settings.EDXAPP_CONFIG.get(
        'MAX_BOOKMARKS_PER_COURSE',
        settings.MAX_BOOKMARKS_PER_COURSE
    )
