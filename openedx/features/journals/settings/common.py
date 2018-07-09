'''Common Settings for Journals'''


def plugin_settings(settings):
    settings.JOURNALS_URL_ROOT = None
    settings.JOURNALS_API_URL = None
    settings.MAKO_TEMPLATE_DIRS_BASE.append(settings.OPENEDX_ROOT / 'features' / 'journals' / 'templates')
    settings.FEATURES['ENABLE_JOURNAL_INTEGRATION'] = False
