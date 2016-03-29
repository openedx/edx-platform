from .devstack import *

INSTALLED_APPS += ('appsembler_cms', 'appsembler_lms',)

APPSEMBLER_SECRET_KEY = "secret_key"
OAUTH_ENFORCE_SECURE = False

# disable caching in dev environment
CACHES['general']['BACKEND'] = 'django.core.cache.backends.dummy.DummyCache'
CACHES['default']['BACKEND'] = 'django.core.cache.backends.dummy.DummyCache'
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

MICROSITE_BACKEND = 'microsite_configuration.backends.database.DatabaseMicrositeBackend'
