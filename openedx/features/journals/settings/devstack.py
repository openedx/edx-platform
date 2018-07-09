'''devstack settings for Journals'''


def plugin_settings(settings):
    settings.JOURNALS_URL_ROOT = 'http://localhost:18606'
    settings.JOURNALS_API_URL = 'http://journals.app:18606/api/v1/'
    settings.FEATURES['ENABLE_JOURNAL_INTEGRATION'] = True
