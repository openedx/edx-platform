'''AWS Settings for Journals'''


def plugin_settings(settings):
    """
    Settings for AWS/Production
    """
    settings.JOURNALS_URL_ROOT = settings.ENV_TOKENS.get('JOURNALS_URL_ROOT', settings.JOURNALS_URL_ROOT)
    settings.JOURNALS_FRONTEND_URL = settings.ENV_TOKENS.get('JOURNALS_FRONTEND_URL', settings.JOURNALS_FRONTEND_URL)
    settings.JOURNALS_API_URL = settings.ENV_TOKENS.get('JOURNALS_API_URL', settings.JOURNALS_API_URL)
    settings.COURSE_CATALOG_URL_BASE = settings.ENV_TOKENS.get(
        'COURSE_CATALOG_URL_BASE', settings.COURSE_CATALOG_URL_BASE)
