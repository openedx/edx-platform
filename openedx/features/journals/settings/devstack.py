'''devstack settings for Journals'''


def plugin_settings(settings):
    """
    Devstack settings for Journals
    """
    settings.JOURNALS_URL_ROOT = 'http://localhost:18606'
    settings.JOURNALS_FRONTEND_URL = 'http://localhost:1991'
    settings.JOURNALS_API_URL = 'http://journals.app:18606/api/v1/'
    settings.FEATURES['JOURNALS_ENABLED'] = True
    settings.COURSE_CATALOG_URL_BASE = 'http://edx.devstack.discovery:18381'
