from .devstack import *

FEATURES['APPSEMBLER_SECRET_KEY'] = "secret_key"
FEATURES['APPSEMBLER_AMC_API_BASE'] = 'http://localhost:8080/api'
FEATURES['APPSEMBLER_FIRST_LOGIN_API'] = '/logged_into_edx'
OAUTH_ENFORCE_SECURE = False

# disable caching in dev environment
#CACHES['general']['BACKEND'] = 'django.core.cache.backends.dummy.DummyCache'
#CACHES['default']['BACKEND'] = 'django.core.cache.backends.dummy.DummyCache'
