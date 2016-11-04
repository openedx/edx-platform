# devstack_appsembler.py

from .devstack import *
from .appsembler import *

INSTALLED_APPS += (
    'appsembler',
    'openedx.core.djangoapps.appsembler.sites',
)

APPSEMBLER_SECRET_KEY = "secret_key"
OAUTH_ENFORCE_SECURE = False

# disable caching in dev environment
CACHES['general']['BACKEND'] = 'django.core.cache.backends.dummy.DummyCache'
CACHES['default']['BACKEND'] = 'django.core.cache.backends.dummy.DummyCache'
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

MICROSITE_BACKEND = 'microsite_configuration.backends.database.DatabaseMicrositeBackend'

DEFAULT_TEMPLATE_ENGINE['OPTIONS']['context_processors'] += ('appsembler.context_processors.intercom',)
