"""
Bare minimum settings for collecting production assets.
"""
from .production import *
from openedx.core.lib.derived import derive_settings

STATICFILES_STORAGE = 'openedx.core.storage.ProductionStorage'
STATIC_URL_BASE = '/static/'
STATIC_ROOT_BASE = '/openedx/staticfiles'
STATIC_ROOT = path(STATIC_ROOT_BASE) / 'studio'
WEBPACK_LOADER['DEFAULT']['STATS_FILE'] = STATIC_ROOT / 'webpack-stats.json'

derive_settings(__name__)

LOCALE_PATHS.append('/openedx/locale/contrib/locale')
LOCALE_PATHS.append('/openedx/locale/user/locale')
