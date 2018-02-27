from .aws import *
import dj_database_url

from django.utils.translation import ugettext_lazy as _

APPSEMBLER_AMC_API_BASE = AUTH_TOKENS.get('APPSEMBLER_AMC_API_BASE')
APPSEMBLER_FIRST_LOGIN_API = '/logged_into_edx'

APPSEMBLER_SECRET_KEY = AUTH_TOKENS.get("APPSEMBLER_SECRET_KEY")

INSTALLED_APPS += (
    'openedx.core.djangoapps.appsembler.sites',
    'openedx.core.djangoapps.appsembler.html_certificates',
)

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

MANDRILL_API_KEY = AUTH_TOKENS.get("MANDRILL_API_KEY")

AMC_APP_URL = ENV_TOKENS.get('AMC_APP_URL')

if MANDRILL_API_KEY:
    EMAIL_BACKEND = ENV_TOKENS.get('EMAIL_BACKEND', 'anymail.backends.mandrill.MandrillBackend')
    ANYMAIL = {
        "MANDRILL_API_KEY": MANDRILL_API_KEY,
    }
    INSTALLED_APPS += ("anymail",)

INTERCOM_APP_ID = AUTH_TOKENS.get("INTERCOM_APP_ID")
INTERCOM_APP_SECRET = AUTH_TOKENS.get("INTERCOM_APP_SECRET")

FEATURES['ENABLE_COURSEWARE_INDEX'] = True
FEATURES['ENABLE_LIBRARY_INDEX'] = True

SEARCH_ENGINE = "search.elastic.ElasticSearchEngine"
ELASTIC_FIELD_MAPPINGS = {
    "start_date": {
        "type": "date"
    }
}

# SENTRY
SENTRY_DSN = AUTH_TOKENS.get('SENTRY_DSN', False)

if SENTRY_DSN:
    # Set your DSN value
    RAVEN_CONFIG = {
        'environment': FEATURES['ENVIRONMENT'],  # This should be moved somewhere more sensible
        'tags': {
            'app': 'edxapp',
            'service': 'cms'
        },
        'dsn': SENTRY_DSN,
    }

    INSTALLED_APPS += ('raven.contrib.django.raven_compat',)

INSTALLED_APPS += (
    'hijack',
    'compat',
    'hijack_admin',
)
MIDDLEWARE_CLASSES += (
    'organizations.middleware.OrganizationMiddleware',
)

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

XQUEUE_WAITTIME_BETWEEN_REQUESTS = 5

CLONE_COURSE_FOR_NEW_SIGNUPS = False
HIJACK_ALLOW_GET_REQUESTS = True
HIJACK_LOGOUT_REDIRECT_URL = '/admin/auth/user'

DEFAULT_COURSE_MODE_SLUG = ENV_TOKENS.get('EDXAPP_DEFAULT_COURSE_MODE_SLUG', 'audit')
DEFAULT_MODE_NAME_FROM_SLUG = _(DEFAULT_COURSE_MODE_SLUG.capitalize())
