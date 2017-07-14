from .aws import *
import dj_database_url

APPSEMBLER_AMC_API_BASE = AUTH_TOKENS.get('APPSEMBLER_AMC_API_BASE')
APPSEMBLER_FIRST_LOGIN_API = '/logged_into_edx'

AMC_APP_URL = ENV_TOKENS.get('AMC_APP_URL')

INSTALLED_APPS += (
    'openedx.core.djangoapps.appsembler.sites',
)

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

if MANDRILL_API_KEY:
    EMAIL_BACKEND = ENV_TOKENS.get('EMAIL_BACKEND', 'anymail.backends.mandrill.MandrillBackend')
    ANYMAIL = {
        "MANDRILL_API_KEY": MANDRILL_API_KEY,
    }
    INSTALLED_APPS += ("anymail",)

INTERCOM_APP_ID = AUTH_TOKENS.get("INTERCOM_APP_ID")
INTERCOM_APP_SECRET = AUTH_TOKENS.get("INTERCOM_APP_SECRET")


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

SEARCH_ENGINE = "search.elastic.ElasticSearchEngine"
SEARCH_INITIALIZER = "lms.lib.courseware_search.lms_search_initializer.LmsSearchInitializer"
SEARCH_RESULT_PROCESSOR = "lms.lib.courseware_search.lms_result_processor.LmsSearchResultProcessor"
SEARCH_FILTER_GENERATOR = "lms.lib.courseware_search.lms_filter_generator.LmsSearchFilterGenerator"

#enable course visibility feature flags
COURSE_CATALOG_VISIBILITY_PERMISSION = 'see_in_catalog'
COURSE_ABOUT_VISIBILITY_PERMISSION = 'see_about_page'
SEARCH_SKIP_ENROLLMENT_START_DATE_FILTERING = True

# disable for now
AUTHENTICATION_BACKENDS = (
    'organizations.backends.DefaultSiteBackend',
    'organizations.backends.SiteMemberBackend',
    'organizations.backends.OrganizationMemberBackend',
)

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

# SENTRY
SENTRY_DSN = AUTH_TOKENS.get('SENTRY_DSN', False)

if SENTRY_DSN:
    # Set your DSN value
    RAVEN_CONFIG = {
        'environment': FEATURES['ENVIRONMENT'],  # This should be moved somewhere more sensible
        'tags': {
            'app': 'edxapp',
            'service': 'lms'
        },
        'dsn': SENTRY_DSN,
    }

    INSTALLED_APPS += ('raven.contrib.django.raven_compat',)

# This is used in the appsembler_sites.middleware.RedirectMiddleware to exclude certain paths
# from the redirect mechanics.
MAIN_SITE_REDIRECT_WHITELIST = ['api', 'admin', 'oauth', 'status']

INSTALLED_APPS += (
    'hijack',
    'compat',
    'hijack_admin',
)
MIDDLEWARE_CLASSES += (
    'tiers.middleware.TierMiddleware',
)

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

if FEATURES.get("ENABLE_TIERS_APP", True):
    TIERS_ORGANIZATION_MODEL = 'organizations.Organization'
    TIERS_EXPIRED_REDIRECT_URL = None
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

CLONE_COURSE_FOR_NEW_SIGNUPS = False
HIJACK_ALLOW_GET_REQUESTS = True
HIJACK_LOGOUT_REDIRECT_URL = '/admin/auth/user'

USE_S3_FOR_CUSTOMER_THEMES = True
