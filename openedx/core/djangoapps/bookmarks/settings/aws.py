def plugin_settings(settings):
    # Course Content Bookmarks Settings
    settings.MAX_BOOKMARKS_PER_COURSE = settings.ENV_TOKENS.get(
        'MAX_BOOKMARKS_PER_COURSE',
        settings.MAX_BOOKMARKS_PER_COURSE
    )
