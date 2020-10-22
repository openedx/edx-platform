'''Test Settings for Journals'''


def plugin_settings(settings):  # pylint ignore:Unused argument
    """
    Test settings for Journals
    """
    settings.COURSE_CATALOG_URL_BASE = 'https://catalog.example.com'
    settings.FEATURES['JOURNALS_ENABLED'] = False
