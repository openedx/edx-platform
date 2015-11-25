# devstack_appsembler.py

from .devstack import *
from .appsembler import *

INSTALLED_APPS += ('appsembler',)
TEMPLATE_CONTEXT_PROCESSORS += ('appsembler.context_processors.intercom',)

FEATURES['APPSEMBLER_SECRET_KEY'] = "secret_key"
OAUTH_ENFORCE_SECURE = False

# disable caching in dev environment
#CACHES['general']['BACKEND'] = 'django.core.cache.backends.dummy.DummyCache'
#CACHES['default']['BACKEND'] = 'django.core.cache.backends.dummy.DummyCache'
