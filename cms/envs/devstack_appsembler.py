# devstack_appsembler.py

from .devstack import *
from .appsembler import *

INSTALLED_APPS += (
    'appsembler',
    'openedx.core.djangoapps.appsembler.sites',
)

# needed to show only users and appsembler courses
FEATURES["ENABLE_COURSE_DISCOVERY"] = True
FEATURES["ENABLE_COMPREHENSIVE_THEMING"] = True
FEATURES["ORGANIZATIONS_APP"] = True
OAUTH_ENFORCE_SECURE = False

APPSEMBLER_SECRET_KEY = "secret_key"

# disable caching in dev environment
for cache_key in CACHES.keys():
    CACHES[cache_key]['BACKEND'] = 'django.core.cache.backends.dummy.DummyCache'

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

MICROSITE_BACKEND = 'microsite_configuration.backends.database.DatabaseMicrositeBackend'

DEFAULT_TEMPLATE_ENGINE['OPTIONS']['context_processors'] += ('openedx.core.djangoapps.appsembler.intercom_integration.context_processors.intercom',)

INTERCOM_APP_ID = AUTH_TOKENS.get("INTERCOM_APP_ID")
INTERCOM_APP_SECRET = AUTH_TOKENS.get("INTERCOM_APP_SECRET")
