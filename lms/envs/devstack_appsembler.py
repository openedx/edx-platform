# devstack_appsembler.py

from .devstack import *
from .appsembler import *
import dj_database_url

OAUTH_ENFORCE_SECURE = False

# disable caching in dev environment
for cache_key in CACHES.keys():
    # CACHES[cache_key]['BACKEND'] = 'django.core.cache.backends.dummy.DummyCache'
    CACHES[cache_key]['BACKEND'] = 'django.core.cache.backends.db.DatabaseCache'
    CACHES[cache_key]['LOCATION'] = 'cache_{}'.format(cache_key)

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

INSTALLED_APPS += (
    'django_extensions',
    'openedx.core.djangoapps.appsembler.sites',
)

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

#SITE_ID = 1

AUTHENTICATION_BACKENDS = (
    'organizations.backends.DefaultSiteBackend',
    'organizations.backends.SiteMemberBackend',
    'organizations.backends.OrganizationMemberBackend',
)

INTERCOM_APP_ID = AUTH_TOKENS.get("INTERCOM_APP_ID")
INTERCOM_APP_SECRET = AUTH_TOKENS.get("INTERCOM_APP_SECRET")

EDX_API_KEY = "test"

INSTALLED_APPS += ('tiers',)
MIDDLEWARE_CLASSES += (
    'organizations.middleware.OrganizationMiddleware',
#    'tiers.middleware.TierMiddleware',
)

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

TIERS_ORGANIZATION_MODEL = 'organizations.Organization'
TIERS_EXPIRED_REDIRECT_URL = None

TIERS_DATABASE_URL = AUTH_TOKENS.get('TIERS_DATABASE_URL')
DATABASES['tiers'] = dj_database_url.parse(TIERS_DATABASE_URL)

DATABASE_ROUTERS += ['openedx.core.djangoapps.appsembler.sites.routers.TiersDbRouter']

COURSE_TO_CLONE = "course-v1:Appsembler+CC101+2017"

CELERY_ALWAYS_EAGER = True

ALTERNATE_QUEUE_ENVS = ['cms']
ALTERNATE_QUEUES = [
    DEFAULT_PRIORITY_QUEUE.replace(QUEUE_VARIANT, alternate + '.')
    for alternate in ALTERNATE_QUEUE_ENVS
]
CELERY_QUEUES.update(
    {
        alternate: {}
        for alternate in ALTERNATE_QUEUES
        if alternate not in CELERY_QUEUES.keys()
    }
)
