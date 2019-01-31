# devstack_appsembler.py

from .devstack import *
from .appsembler import *
import dj_database_url

from django.utils.translation import ugettext_lazy as _

OAUTH_ENFORCE_SECURE = False

# disable caching in dev environment
for cache_key in CACHES.keys():
    CACHES[cache_key]['BACKEND'] = 'django.core.cache.backends.dummy.DummyCache'

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

INSTALLED_APPS += (
    'django_extensions',
    'openedx.core.djangoapps.appsembler.sites',
    'openedx.core.djangoapps.appsembler.msft_lp',
    'openedx.core.djangoapps.appsembler.tpa_admin',
    'openedx.core.djangoapps.appsembler.html_certificates',
    'openedx.core.djangoapps.appsembler.api',
)

# those are usually hardcoded in devstack.py for some reason
LMS_BASE = ENV_TOKENS.get('LMS_BASE')
LMS_ROOT_URL = ENV_TOKENS.get('LMS_ROOT_URL')

APPSEMBLER_FEATURES = ENV_TOKENS.get('APPSEMBLER_FEATURES', {})

GOOGLE_ANALYTICS_APP_ID = AUTH_TOKENS.get('GOOGLE_ANALYTICS_APP_ID')
HUBSPOT_API_KEY = AUTH_TOKENS.get('HUBSPOT_API_KEY')
HUBSPOT_PORTAL_ID = AUTH_TOKENS.get('HUBSPOT_PORTAL_ID')
MIXPANEL_APP_ID = AUTH_TOKENS.get('MIXPANEL_APP_ID')

DEFAULT_TEMPLATE_ENGINE['OPTIONS']['context_processors'] += (
    'openedx.core.djangoapps.appsembler.intercom_integration.context_processors.intercom',
    'openedx.core.djangoapps.appsembler.analytics.context_processors.google_analytics',
    'openedx.core.djangoapps.appsembler.analytics.context_processors.hubspot',
    'openedx.core.djangoapps.appsembler.analytics.context_processors.mixpanel',
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

INSTALLED_APPS += (
    'hijack',
    'compat',
    'hijack_admin',
)
MIDDLEWARE_CLASSES += (
    'organizations.middleware.OrganizationMiddleware',
)

COURSE_CATALOG_VISIBILITY_PERMISSION = 'see_in_catalog'
COURSE_ABOUT_VISIBILITY_PERMISSION = 'see_about_page'
SEARCH_SKIP_ENROLLMENT_START_DATE_FILTERING = True

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

if FEATURES.get("ENABLE_TIERS_APP", True):
    TIERS_ORGANIZATION_MODEL = 'organizations.Organization'
    TIERS_EXPIRED_REDIRECT_URL = ENV_TOKENS.get('TIERS_EXPIRED_REDIRECT_URL', None)
    TIERS_ORGANIZATION_TIER_GETTER_NAME = 'get_tier_for_org'

    TIERS_DATABASE_URL = AUTH_TOKENS.get('TIERS_DATABASE_URL')
    DATABASES['tiers'] = dj_database_url.parse(TIERS_DATABASE_URL)
    DATABASE_ROUTERS += ['openedx.core.djangoapps.appsembler.sites.routers.TiersDbRouter']

    MIDDLEWARE_CLASSES += (
        'tiers.middleware.TierMiddleware',
    )

    INSTALLED_APPS += (
        'tiers',
    )

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

CLONE_COURSE_FOR_NEW_SIGNUPS = False
HIJACK_ALLOW_GET_REQUESTS = True
HIJACK_LOGOUT_REDIRECT_URL = '/admin/auth/user'

USE_S3_FOR_CUSTOMER_THEMES = False

LMS_BASE = ENV_TOKENS.get('LMS_BASE')

if FEATURES.get('ENABLE_THIRD_PARTY_AUTH'):
    AUTHENTICATION_BACKENDS = list(AUTHENTICATION_BACKENDS) + (
        ENV_TOKENS.get('THIRD_PARTY_AUTH_BACKENDS', [
            'social.backends.google.GoogleOAuth2',
            'social.backends.linkedin.LinkedinOAuth2',
            'social.backends.facebook.FacebookOAuth2',
            'social.backends.azuread.AzureADOAuth2',
            'third_party_auth.saml.SAMLAuthBackend',
            'third_party_auth.lti.LTIAuthBackend',
        ])
    )

DEFAULT_COURSE_MODE_SLUG = ENV_TOKENS.get('EDXAPP_DEFAULT_COURSE_MODE_SLUG', 'audit')
DEFAULT_MODE_NAME_FROM_SLUG = _(DEFAULT_COURSE_MODE_SLUG.capitalize())

CUSTOM_DOMAINS_REDIRECT_CACHE_TIMEOUT = None  # The length of time we cache Redirect model data
CUSTOM_DOMAINS_REDIRECT_CACHE_KEY_PREFIX = 'custom_domains_redirects'

try:
    from .private import *
except ImportError:
    pass
