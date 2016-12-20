from .aws import *

APPSEMBLER_SECRET_KEY = AUTH_TOKENS.get("APPSEMBLER_SECRET_KEY")
# the following ip should work for all dev setups....
APPSEMBLER_AMC_API_BASE = AUTH_TOKENS.get('APPSEMBLER_AMC_API_BASE')
APPSEMBLER_FIRST_LOGIN_API = '/logged_into_edx'

# needed to show only users and appsembler courses
#FEATURES["ENABLE_COURSE_DISCOVERY"] = False
FEATURES["ORGANIZATIONS_APP"] = True
FEATURES["ENABLE_COMPREHENSIVE_THEMING"] = True

INSTALLED_APPS += (
    'openedx.core.djangoapps.appsembler.sites',
)

EMAIL_BACKEND = 'django_mailgun.MailgunBackend'
MAILGUN_ACCESS_KEY = AUTH_TOKENS.get("MAILGUN_ACCESS_KEY")
MAILGUN_SERVER_NAME = AUTH_TOKENS.get("MAILGUN_SERVER_NAME")

# disable caching in dev environment
for cache_key in CACHES.keys():
    CACHES[cache_key]['BACKEND'] = 'django.core.cache.backends.dummy.DummyCache'

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

MICROSITE_BACKEND = 'microsite_configuration.backends.database.DatabaseMicrositeBackend'

STATICFILES_STORAGE = 'openedx.core.storage.DevelopmentStorage'

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

FEATURES['ENABLE_COURSEWARE_SEARCH'] = True
FEATURES['ENABLE_DASHBOARD_SEARCH'] = True
FEATURES['ENABLE_COURSE_DISCOVERY'] = True

SEARCH_ENGINE = "search.elastic.ElasticSearchEngine"
SEARCH_INITIALIZER = "lms.lib.courseware_search.lms_search_initializer.LmsSearchInitializer"
SEARCH_RESULT_PROCESSOR = "lms.lib.courseware_search.lms_result_processor.LmsSearchResultProcessor"
SEARCH_FILTER_GENERATOR = "lms.lib.courseware_search.lms_filter_generator.LmsSearchFilterGenerator"

SEARCH_SKIP_ENROLLMENT_START_DATE_FILTERING = True

# disable for now
#AUTHENTICATION_BACKENDS = ('organizations.backends.OrganizationMemberBackend',) + AUTHENTICATION_BACKENDS
