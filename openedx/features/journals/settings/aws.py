'''AWS Settings for Journals'''


def plugin_settings(settings):
    settings.JOURNALS_URL_ROOT = settings.ENV_TOKENS.get('JOURNALS_URL_ROOT', settings.JOURNALS_URL_ROOT)
    settings.JOURNALS_API_URL = settings.ENV_TOKENS.get('JOURNALS_API_URL', settings.JOURNALS_API_URL)
