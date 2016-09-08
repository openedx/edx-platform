from .devstack import *

APPSEMBLER_SECRET_KEY = "secret_key"
# the following ip should work for all dev setups....
APPSEMBLER_AMC_API_BASE = 'http://10.0.2.2:8080/api'
APPSEMBLER_FIRST_LOGIN_API = '/logged_into_edx'

FEATURES["ENABLE_SYSADMIN_DASHBOARD"] = True

# needed to show only users and appsembler courses
FEATURES["ENABLE_COURSE_DISCOVERY"] = True
FEATURES["ORGANIZATIONS_APP"] = True
OAUTH_ENFORCE_SECURE = False

# disable caching in dev environment
for cache_key in CACHES.keys():
    CACHES[cache_key]['BACKEND'] = 'django.core.cache.backends.dummy.DummyCache'

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

MICROSITE_BACKEND = 'microsite_configuration.backends.database.DatabaseMicrositeBackend'

INSTALLED_APPS += ('appsembler_lms',)

CORS_ORIGIN_ALLOW_ALL = True

CORS_ALLOW_HEADERS = (
    'x-requested-with',
    'content-type',
    'accept',
    'origin',
    'authorization',
    'x-csrftoken',
    'cache-control'
)
DEBUG_TOOLBAR_PATCH_SETTINGS = False

# MIDDLEWARE_CLASSES = (
#     'db_multitenant.middleware.MultiTenantMiddleware',
#     ) + MIDDLEWARE_CLASSES
#
# SOUTH_DATABASE_ADAPTERS = {
#     'default': 'south.db.mysql'
# }
#
# MULTITENANT_MAPPER_CLASS = 'microsite_configuration.mapper.SimpleTenantMapper'

#DATABASES['default']['ENGINE'] = 'db_multitenant.db.backends.mysql'
