'''Common Settings for Journals'''


def plugin_settings(settings):
    """
    Common settings for Journals
    """
    settings.JOURNALS_URL_ROOT = None
    settings.JOURNALS_FRONTEND_URL = None
    settings.JOURNALS_API_URL = None
    settings.FEATURES['JOURNALS_ENABLED'] = False
    settings.COURSE_CATALOG_URL_BASE = None
    settings.MAKO_TEMPLATE_DIRS_BASE.append(settings.OPENEDX_ROOT / 'features' / 'journals' / 'templates')
