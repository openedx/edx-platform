"""
This is the default template for our main set of AWS servers.

Common traits:
* Use memcached, and cache-backed sessions
* Use a MySQL 5.1 database
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=wildcard-import, unused-wildcard-import

# Pylint gets confused by path.py instances, which report themselves as class
# objects. As a result, pylint applies the wrong regex in validating names,
# and throws spurious errors. Therefore, we disable invalid-name checking.
# pylint: disable=invalid-name


import codecs
import copy
import datetime
import os

import yaml
import django
from django.core.exceptions import ImproperlyConfigured
from edx_django_utils.plugins import add_plugins
from openedx_events.event_bus import merge_producer_configs
from path import Path as path

from openedx.core.djangoapps.plugins.constants import ProjectType, SettingsType
from openedx.core.lib.derived import derive_settings
from openedx.core.lib.logsettings import get_logger_config
from xmodule.modulestore.modulestore_settings import convert_module_store_setting_if_needed  # lint-amnesty, pylint: disable=wrong-import-order

from .common import *


def get_env_setting(setting):
    """ Get the environment setting or return exception """
    try:
        return os.environ[setting]
    except KeyError:
        error_msg = "Set the %s env variable" % setting
        raise ImproperlyConfigured(error_msg)  # lint-amnesty, pylint: disable=raise-missing-from


######################### PRODUCTION DEFAULTS ##############################

DEBUG = False
DEFAULT_TEMPLATE_ENGINE['OPTIONS']['debug'] = False

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

# IMPORTANT: With this enabled, the server must always be behind a proxy that
# strips the header HTTP_X_FORWARDED_PROTO from client requests. Otherwise,
# a user can fool our server into thinking it was an https connection.
# See
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
# for other warnings.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

###################################### MOVED UP  ################################

CELERY_RESULT_BACKEND = 'django-cache'
BROKER_HEARTBEAT = 60.0
BROKER_HEARTBEAT_CHECKRATE = 2
STATIC_ROOT_BASE = None
STATIC_URL_BASE = ENV_TOKENS.get('STATIC_URL_BASE', None)
EMAIL_FILE_PATH = DATA_DIR / "emails" / "lms"
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
EMAIL_USE_TLS = False
SESSION_COOKIE_DOMAIN = None
SESSION_COOKIE_HTTPONLY = True
AWS_SES_REGION_NAME = 'us-east-1'
AWS_SES_REGION_ENDPOINT = 'email.us-east-1.amazonaws.com'
REGISTRATION_EMAIL_PATTERNS_ALLOWED = None
LMS_ROOT_URL = None
CMS_BASE = 'studio.edx.org'
CELERY_EVENT_QUEUE_TTL = None
# COMPREHENSIVE_THEME_LOCALE_PATHS contain the paths to themes locale directories e.g.
# "COMPREHENSIVE_THEME_LOCALE_PATHS" : [
#        "/edx/src/edx-themes/conf/locale"
#    ],
COMPREHENSIVE_THEME_LOCALE_PATHS = ENV_TOKENS.get('COMPREHENSIVE_THEME_LOCALE_PATHS', [])
# PREPEND_LOCALE_PATHS contain the paths to locale directories to load first e.g.
# "PREPEND_LOCALE_PATHS" : [
#        "/edx/my-locale"
#    ],
PREPEND_LOCALE_PATHS = ENV_TOKENS.get('PREPEND_LOCALE_PATHS', [])
COURSE_LISTINGS = {}
COMMENTS_SERVICE_URL = ''
COMMENTS_SERVICE_KEY = ''
CERT_QUEUE = 'test-pull'
PYTHON_LIB_FILENAME = 'python_lib.zip'
VIDEO_CDN_URL = {}
HOSTNAME_MODULESTORE_DEFAULT_MAPPINGS = {}
AWS_STORAGE_BUCKET_NAME = 'edxuploads'
# Disabling querystring auth instructs Boto to exclude the querystring parameters (e.g. signature, access key) it
# normally appends to every returned URL.
AWS_QUERYSTRING_AUTH = True
AWS_S3_CUSTOM_DOMAIN = 'edxuploads.s3.amazonaws.com'
MONGODB_LOG = {}
ZENDESK_USER = None
ZENDESK_API_KEY = None
EDX_API_KEY = None
CELERY_BROKER_TRANSPORT = ""
CELERY_BROKER_HOSTNAME = ""
CELERY_BROKER_VHOST = ""
CELERY_BROKER_USER = ""
CELERY_BROKER_PASSWORD = ""
BROKER_USE_SSL = False
SESSION_INACTIVITY_TIMEOUT_IN_SECONDS = None
ENABLE_REQUIRE_THIRD_PARTY_AUTH = False

# TODO make a note about axing these
# SSL external authentication settings
SSL_AUTH_EMAIL_DOMAIN = "MIT.EDU"
SSL_AUTH_DN_FORMAT_STRING = (
    "/C=US/ST=Massachusetts/O=Massachusetts Institute of Technology/OU=Client CA v1/CN={0}/emailAddress={1}"
)

###########################################################################

# A file path to a YAML file from which to load all the configuration for the edx platform
CONFIG_FILE = get_env_setting('LMS_CFG')

with codecs.open(CONFIG_FILE, encoding='utf-8') as f:
    __config__ = yaml.safe_load(f)

    # ENV_TOKENS and AUTH_TOKENS are included for reverse compatibility.
    # Removing them may break plugins that rely on them.
    ENV_TOKENS = __config__
    AUTH_TOKENS = __config__

    # _YAML_TOKENS is used strategically to handle YAML config files in a backwards-compatible way.
    # Please do not add more references to it.
    # See: < TODO TICKET LINK >
    _YAML_TOKENS = __config__

    # Add the key/values from config into the global namespace of this module.
    # But don't override the FEATURES dict because we do that in an additive way.
    __config_copy__ = copy.deepcopy(__config__)

    KEYS_WITH_MERGED_VALUES = [
        'FEATURES',
        'TRACKING_BACKENDS',
        'EVENT_TRACKING_BACKENDS',
        'JWT_AUTH',
        'CELERY_QUEUES',
        'MKTG_URL_LINK_MAP',
        'REST_FRAMEWORK',
        'EVENT_BUS_PRODUCER_CONFIG',
    ]
    for key in KEYS_WITH_MERGED_VALUES:
        if key in __config_copy__:
            del __config_copy__[key]

    vars().update(__config_copy__)


try:
    # A file path to a YAML file from which to load all the code revisions currently deployed
    REVISION_CONFIG_FILE = get_env_setting('REVISION_CFG')

    with codecs.open(REVISION_CONFIG_FILE, encoding='utf-8') as f:
        REVISION_CONFIG = yaml.safe_load(f)
except Exception:  # pylint: disable=broad-except
    REVISION_CONFIG = {}

# Do NOT calculate this dynamically at startup with git because it's *slow*.
EDX_PLATFORM_REVISION = REVISION_CONFIG.get('EDX_PLATFORM_REVISION', EDX_PLATFORM_REVISION)

###################################### CELERY  ################################

# Don't use a connection pool, since connections are dropped by ELB.
BROKER_POOL_LIMIT = 0
BROKER_CONNECTION_TIMEOUT = 1

# Each worker should only fetch one message at a time
CELERYD_PREFETCH_MULTIPLIER = 1

# STATIC_ROOT specifies the directory where static files are
# collected
if STATIC_ROOT_BASE:
    STATIC_ROOT = path(STATIC_ROOT_BASE)
    WEBPACK_LOADER['DEFAULT']['STATS_FILE'] = STATIC_ROOT / "webpack-stats.json"
    WEBPACK_LOADER['WORKERS']['STATS_FILE'] = STATIC_ROOT / "webpack-worker-stats.json"


# STATIC_URL_BASE specifies the base url to use for static files
if STATIC_URL_BASE:
    STATIC_URL = STATIC_URL_BASE
    if not STATIC_URL.endswith("/"):
        STATIC_URL += "/"

DATA_DIR = path(DATA_DIR)
CC_MERCHANT_NAME = _YAML_TOKENS.get('CC_MERCHANT_NAME', PLATFORM_NAME)

# TODO comment about this being for backcompat with yaml
SESSION_COOKIE_SAMESITE = DCS_SESSION_COOKIE_SAMESITE

LMS_INTERNAL_ROOT_URL = _YAML_TOKENS.get('LMS_INTERNAL_ROOT_URL', LMS_ROOT_URL)

for feature, value in _YAML_TOKENS.get('FEATURES', {}).items():
    FEATURES[feature] = value

ALLOWED_HOSTS = [
    "*",
    _YAML_TOKENS.get('LMS_BASE'),
    FEATURES['PREVIEW_LMS_BASE'],
]

# This is the domain that is used to set shared cookies between various sub-domains.
# By default, it's set to the same thing as the SESSION_COOKIE_DOMAIN, but we want to make it overrideable.
SHARED_COOKIE_DOMAIN = _YAML_TOKENS.get('SHARED_COOKIE_DOMAIN', SESSION_COOKIE_DOMAIN)

# Cache used for location mapping -- called many times with the same key/value
# in a given request.
if 'loc_cache' not in CACHES:
    CACHES['loc_cache'] = {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'edx_location_mem_cache',
    }

if 'staticfiles' in CACHES:
    CACHES['staticfiles']['KEY_PREFIX'] = EDX_PLATFORM_REVISION

# In order to transition from local disk asset storage to S3 backed asset storage,
# we need to run asset collection twice, once for local disk and once for S3.
# Once we have migrated to service assets off S3, then we can convert this back to
# managed by the yaml file contents

# We want Bulk Email running on the high-priority queue, so we define the
# routing key that points to it. At the moment, the name is the same.
# We have to reset the value here, since we have changed the value of the queue name.
BULK_EMAIL_ROUTING_KEY = _YAML_TOKENS.get('BULK_EMAIL_ROUTING_KEY', HIGH_PRIORITY_QUEUE)

# We can run smaller jobs on the low priority queue. See note above for why
# we have to reset the value here.
BULK_EMAIL_ROUTING_KEY_SMALL_JOBS = _YAML_TOKENS.get('BULK_EMAIL_ROUTING_KEY_SMALL_JOBS', DEFAULT_PRIORITY_QUEUE)

# Queue to use for expiring old entitlements
ENTITLEMENTS_EXPIRATION_ROUTING_KEY = _YAML_TOKENS.get('ENTITLEMENTS_EXPIRATION_ROUTING_KEY', DEFAULT_PRIORITY_QUEUE)

# Allow CELERY_QUEUES to be overwritten by ENV_TOKENS,
_YAML_CELERY_QUEUES = _YAML_TOKENS.get('CELERY_QUEUES', None)
if _YAML_CELERY_QUEUES:
    CELERY_QUEUES = {queue: {} for queue in _YAML_CELERY_QUEUES}

# Then add alternate environment queues
_YAML_ALTERNATE_WORKER_QUEUES = _YAML_TOKENS.get('ALTERNATE_WORKER_QUEUES', '').split()
ALTERNATE_QUEUES = [
    DEFAULT_PRIORITY_QUEUE.replace(QUEUE_VARIANT, alternate + '.')
    for alternate in _YAML_ALTERNATE_WORKER_QUEUES
]

CELERY_QUEUES.update(
    {
        alternate: {}
        for alternate in ALTERNATE_QUEUES
        if alternate not in CELERY_QUEUES.keys()
    }
)


MKTG_URL_LINK_MAP.update(_YAML_TOKENS.get('MKTG_URL_LINK_MAP', {}))

# Intentional defaults.
ID_VERIFICATION_SUPPORT_LINK = YAML_TOKENS.get('ID_VERIFICATION_SUPPORT_LINK', SUPPORT_SITE_LINK)
PASSWORD_RESET_SUPPORT_LINK = _YAML_TOKENS.get('PASSWORD_RESET_SUPPORT_LINK', SUPPORT_SITE_LINK)
ACTIVATION_EMAIL_SUPPORT_LINK = _YAML_TOKENS.get('ACTIVATION_EMAIL_SUPPORT_LINK', SUPPORT_SITE_LINK)
LOGIN_ISSUE_SUPPORT_LINK = _YAML_TOKENS.get('LOGIN_ISSUE_SUPPORT_LINK', SUPPORT_SITE_LINK)

# Timezone overrides
TIME_ZONE = CELERY_TIMEZONE

# Translation overrides
LANGUAGE_DICT = dict(LANGUAGES)

# TODO add a comment about LANGUAGE_COOKIE being deprecated / add to notes
LANGUAGE_COOKIE_NAME = _YAML_TOKENS.get('LANGUAGE_COOKIE') or LANGUAGE_COOKIE_NAME

# Additional installed apps
for app in _YAML_TOKENS.get('ADDL_INSTALLED_APPS', []):
    INSTALLED_APPS.append(app)

LOGGING = get_logger_config(
    LOG_DIR,
    logging_env=LOGGING_ENV,
    local_loglevel=LOCAL_LOGLEVEL,
    service_variant=SERVICE_VARIANT,
)

# Determines which origins are trusted for unsafe requests eg. POST requests.
CSRF_TRUSTED_ORIGINS = _YAML_TOKENS.get('CSRF_TRUSTED_ORIGINS_WITH_SCHEME', [])

if FEATURES['ENABLE_CORS_HEADERS'] or FEATURES.get('ENABLE_CROSS_DOMAIN_CSRF_COOKIE'):
    CORS_ALLOW_CREDENTIALS = True
    CORS_ORIGIN_WHITELIST = _YAML_TOKENS.get('CORS_ORIGIN_WHITELIST', ())
    CORS_ORIGIN_ALLOW_ALL = YAML_TOKENS.get('CORS_ORIGIN_ALLOW_ALL', False)
    CORS_ALLOW_INSECURE = _YAML_TOKENS.get('CORS_ALLOW_INSECURE', False)
    CROSS_DOMAIN_CSRF_COOKIE_DOMAIN = ENV_TOKENS.get('CROSS_DOMAIN_CSRF_COOKIE_DOMAIN')

FIELD_OVERRIDE_PROVIDERS = tuple(FIELD_OVERRIDE_PROVIDERS)

# PREVIEW DOMAIN must be present in HOSTNAME_MODULESTORE_DEFAULT_MAPPINGS for the preview to show draft changes
if 'PREVIEW_LMS_BASE' in FEATURES and FEATURES['PREVIEW_LMS_BASE'] != '':
    PREVIEW_DOMAIN = FEATURES['PREVIEW_LMS_BASE'].split(':')[0]
    # update dictionary with preview domain regex
    HOSTNAME_MODULESTORE_DEFAULT_MAPPINGS.update({
        PREVIEW_DOMAIN: 'draft-preferred'
    })

############### Mixed Related(Secure/Not-Secure) Items ##########
LMS_SEGMENT_KEY = _YAML_TOKENS.get('SEGMENT_KEY')

if AWS_ACCESS_KEY_ID == "":
    AWS_ACCESS_KEY_ID = None
if AWS_SECRET_ACCESS_KEY == "":
    AWS_SECRET_ACCESS_KEY = None

# these variable already exists in cms with `private` value. django-storages starting `1.10.1`
# does not set acl values till 1.9.1 default-acl is `public-read`. To maintain the behaviour
# same with upcoming version setting it to `public-read`.
AWS_DEFAULT_ACL = 'public-read'
AWS_BUCKET_ACL = AWS_DEFAULT_ACL

# Change to S3Boto3 if we haven't specified another default storage AND we have specified AWS creds.
if (not _YAML_TOKENS.get('DEFAULT_FILE_STORAGE')) and AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# The normal database user does not have enough permissions to run migrations.
# Migrations are run with separate credentials, given as DB_MIGRATION_*
# environment variables
for name, database in DATABASES.items():
    if name != 'read_replica':
        database.update({
            'ENGINE': os.environ.get('DB_MIGRATION_ENGINE', database['ENGINE']),
            'USER': os.environ.get('DB_MIGRATION_USER', database['USER']),
            'PASSWORD': os.environ.get('DB_MIGRATION_PASS', database['PASSWORD']),
            'NAME': os.environ.get('DB_MIGRATION_NAME', database['NAME']),
            'HOST': os.environ.get('DB_MIGRATION_HOST', database['HOST']),
            'PORT': os.environ.get('DB_MIGRATION_PORT', database['PORT']),
        })

# Get the MODULESTORE from auth.json, but if it doesn't exist,
# use the one from common.py
MODULESTORE = convert_module_store_setting_if_needed(AUTH_TOKENS.get('MODULESTORE', MODULESTORE))

# After conversion above, the modulestore will have a "stores" list with all defined stores, for all stores, add the
# fs_root entry to derived collection so that if it's a callable it can be resolved.  We need to do this because the
# `derived_collection_entry` takes an exact index value but the config file might have overridden the number of stores
# and so we can't be sure that the 2 we define in common.py will be there when we try to derive settings.  This could
# lead to exceptions being thrown when the `derive_settings` call later in this file tries to update settings.  We call
# the derived_collection_entry function here to ensure that we update the fs_root for any callables that remain after
# we've updated the MODULESTORE setting from our config file.
for idx, store in enumerate(MODULESTORE['default']['OPTIONS']['stores']):
    if 'OPTIONS' in store and 'fs_root' in store["OPTIONS"]:
        derived_collection_entry('MODULESTORE', 'default', 'OPTIONS', 'stores', idx, 'OPTIONS', 'fs_root')

BROKER_URL = "{}://{}:{}@{}/{}".format(CELERY_BROKER_TRANSPORT,
                                       CELERY_BROKER_USER,
                                       CELERY_BROKER_PASSWORD,
                                       CELERY_BROKER_HOSTNAME,
                                       CELERY_BROKER_VHOST)
try:
    BROKER_TRANSPORT_OPTIONS = {
        'fanout_patterns': True,
        'fanout_prefix': True,
        **_YAML_TOKENS.get('CELERY_BROKER_TRANSPORT_OPTIONS', {})
    }
except TypeError as exc:
    raise ImproperlyConfigured('CELERY_BROKER_TRANSPORT_OPTIONS must be a dict') from exc

# Event tracking
TRACKING_BACKENDS.update(_YAML_TOKENS.get("TRACKING_BACKENDS", {}))
EVENT_TRACKING_BACKENDS['tracking_logs']['OPTIONS']['backends'].update(
    _YAML_TOKENS.get("EVENT_TRACKING_BACKENDS", {})
)
EVENT_TRACKING_BACKENDS['segmentio']['OPTIONS']['processors'][0]['OPTIONS']['whitelist'].extend(
    EVENT_TRACKING_SEGMENTIO_EMIT_WHITELIST
)

# Grades download
GRADES_DOWNLOAD_ROUTING_KEY = _YAML_TOKENS.get('GRADES_DOWNLOAD_ROUTING_KEY', HIGH_MEM_QUEUE)

if FEATURES.get('ENABLE_THIRD_PARTY_AUTH'):
    AUTHENTICATION_BACKENDS = _YAML_TOKENS.get('THIRD_PARTY_AUTH_BACKENDS', [
        'social_core.backends.google.GoogleOAuth2',
        'social_core.backends.linkedin.LinkedinOAuth2',
        'social_core.backends.facebook.FacebookOAuth2',
        'social_core.backends.azuread.AzureADOAuth2',
        'common.djangoapps.third_party_auth.appleid.AppleIdAuth',  # vendored 'social_core.backends.apple.AppleIdAuth'
        'common.djangoapps.third_party_auth.identityserver3.IdentityServer3',
        'common.djangoapps.third_party_auth.saml.SAMLAuthBackend',
        'common.djangoapps.third_party_auth.lti.LTIAuthBackend',
    ]) + list(AUTHENTICATION_BACKENDS)

    # The reduced session expiry time during the third party login pipeline. (Value in seconds)
    SOCIAL_AUTH_PIPELINE_TIMEOUT = _YAML_TOKENS.get('SOCIAL_AUTH_PIPELINE_TIMEOUT', 600)

    # TODO: just define this in common.py
    SOCIAL_AUTH_LTI_CONSUMER_SECRETS = _YAML_TOKENS.get('SOCIAL_AUTH_LTI_CONSUMER_SECRETS', {})

    # third_party_auth config moved to ConfigurationModels. This is for data migration only:
    THIRD_PARTY_AUTH_OLD_CONFIG = _YAML_TOKENS.get('THIRD_PARTY_AUTH', None)

    # TODO: This logic is somewhat insane. We're not sure if it's intentional or not. We've left it
    # as-is for strict backwards compatibility, but it's worth revisiting.
    if (
        # if we didn't override the value in YAML,
        'THIRD_PARTY_AUTH_SAML_FETCH_PERIOD_HOURS' not in _YAML_TOKENS or
        # OR we overrode it to a truthy value,
        (hours := _YAML_TOKENS.get('THIRD_PARTY_AUTH_SAML_FETCH_PERDIOD_HOURS', 24))
    ):
        # then update CELERYBEAT_SCHEDULE.
        CELERYBEAT_SCHEDULE['refresh-saml-metadata'] = {
            'task': 'common.djangoapps.third_party_auth.fetch_saml_metadata',
            'schedule': datetime.timedelta(hours=hours),
        }

    # The following can be used to integrate a custom login form with third_party_auth.
    # It should be a dict where the key is a word passed via ?auth_entry=, and the value is a
    # dict with an arbitrary 'secret_key' and a 'url'.
    THIRD_PARTY_AUTH_CUSTOM_AUTH_FORMS = _YAML_TOKENS.get('THIRD_PARTY_AUTH_CUSTOM_AUTH_FORMS', {})

##### OAUTH2 Provider ##############
if FEATURES.get('ENABLE_OAUTH2_PROVIDER'):
    OAUTH_ENFORCE_SECURE = ENV_TOKENS.get('OAUTH_ENFORCE_SECURE', True)
    OAUTH_ENFORCE_CLIENT_SECURE = ENV_TOKENS.get('OAUTH_ENFORCE_CLIENT_SECURE', True)
    # Defaults for the following are defined in lms.envs.common
    OAUTH_EXPIRE_DELTA = datetime.timedelta(
        days=ENV_TOKENS.get('OAUTH_EXPIRE_CONFIDENTIAL_CLIENT_DAYS', OAUTH_EXPIRE_CONFIDENTIAL_CLIENT_DAYS)
    )
    OAUTH_EXPIRE_DELTA_PUBLIC = datetime.timedelta(
        days=ENV_TOKENS.get('OAUTH_EXPIRE_PUBLIC_CLIENT_DAYS', OAUTH_EXPIRE_PUBLIC_CLIENT_DAYS)
    )


##### GOOGLE ANALYTICS IDS #####
GOOGLE_ANALYTICS_ACCOUNT = AUTH_TOKENS.get('GOOGLE_ANALYTICS_ACCOUNT')
GOOGLE_ANALYTICS_TRACKING_ID = AUTH_TOKENS.get('GOOGLE_ANALYTICS_TRACKING_ID')
GOOGLE_ANALYTICS_LINKEDIN = AUTH_TOKENS.get('GOOGLE_ANALYTICS_LINKEDIN')
GOOGLE_SITE_VERIFICATION_ID = ENV_TOKENS.get('GOOGLE_SITE_VERIFICATION_ID')
GOOGLE_ANALYTICS_4_ID = AUTH_TOKENS.get('GOOGLE_ANALYTICS_4_ID')

##### BRANCH.IO KEY #####
BRANCH_IO_KEY = AUTH_TOKENS.get('BRANCH_IO_KEY')

#### Course Registration Code length ####
REGISTRATION_CODE_LENGTH = ENV_TOKENS.get('REGISTRATION_CODE_LENGTH', 8)

# Which access.py permission names to check;
# We default this to the legacy permission 'see_exists'.
COURSE_CATALOG_VISIBILITY_PERMISSION = ENV_TOKENS.get(
    'COURSE_CATALOG_VISIBILITY_PERMISSION',
    COURSE_CATALOG_VISIBILITY_PERMISSION
)
COURSE_ABOUT_VISIBILITY_PERMISSION = ENV_TOKENS.get(
    'COURSE_ABOUT_VISIBILITY_PERMISSION',
    COURSE_ABOUT_VISIBILITY_PERMISSION
)

DEFAULT_COURSE_VISIBILITY_IN_CATALOG = ENV_TOKENS.get(
    'DEFAULT_COURSE_VISIBILITY_IN_CATALOG',
    DEFAULT_COURSE_VISIBILITY_IN_CATALOG
)

DEFAULT_MOBILE_AVAILABLE = ENV_TOKENS.get(
    'DEFAULT_MOBILE_AVAILABLE',
    DEFAULT_MOBILE_AVAILABLE
)

# Enrollment API Cache Timeout
ENROLLMENT_COURSE_DETAILS_CACHE_TIMEOUT = ENV_TOKENS.get('ENROLLMENT_COURSE_DETAILS_CACHE_TIMEOUT', 60)

# Ecommerce Orders API Cache Timeout
ECOMMERCE_ORDERS_API_CACHE_TIMEOUT = ENV_TOKENS.get('ECOMMERCE_ORDERS_API_CACHE_TIMEOUT', 3600)

if FEATURES.get('ENABLE_COURSEWARE_SEARCH') or \
   FEATURES.get('ENABLE_DASHBOARD_SEARCH') or \
   FEATURES.get('ENABLE_COURSE_DISCOVERY') or \
   FEATURES.get('ENABLE_TEAMS'):
    # Use ElasticSearch as the search engine herein
    SEARCH_ENGINE = "search.elastic.ElasticSearchEngine"
    SEARCH_FILTER_GENERATOR = ENV_TOKENS.get('SEARCH_FILTER_GENERATOR', SEARCH_FILTER_GENERATOR)

SEARCH_SKIP_INVITATION_ONLY_FILTERING = ENV_TOKENS.get(
    'SEARCH_SKIP_INVITATION_ONLY_FILTERING',
    SEARCH_SKIP_INVITATION_ONLY_FILTERING,
)
SEARCH_SKIP_SHOW_IN_CATALOG_FILTERING = ENV_TOKENS.get(
    'SEARCH_SKIP_SHOW_IN_CATALOG_FILTERING',
    SEARCH_SKIP_SHOW_IN_CATALOG_FILTERING,
)

SEARCH_COURSEWARE_CONTENT_LOG_PARAMS = ENV_TOKENS.get(
    'SEARCH_COURSEWARE_CONTENT_LOG_PARAMS',
    SEARCH_COURSEWARE_CONTENT_LOG_PARAMS,
)

# TODO: Once we have successfully upgraded to ES7, switch this back to ELASTIC_SEARCH_CONFIG.
ELASTIC_SEARCH_CONFIG = ENV_TOKENS.get('ELASTIC_SEARCH_CONFIG_ES7', [{}])

# Facebook app
FACEBOOK_API_VERSION = AUTH_TOKENS.get("FACEBOOK_API_VERSION")
FACEBOOK_APP_SECRET = AUTH_TOKENS.get("FACEBOOK_APP_SECRET")
FACEBOOK_APP_ID = AUTH_TOKENS.get("FACEBOOK_APP_ID")

XBLOCK_SETTINGS = ENV_TOKENS.get('XBLOCK_SETTINGS', {})
XBLOCK_SETTINGS.setdefault("VideoBlock", {})["licensing_enabled"] = FEATURES.get("LICENSING", False)
XBLOCK_SETTINGS.setdefault("VideoBlock", {})['YOUTUBE_API_KEY'] = AUTH_TOKENS.get('YOUTUBE_API_KEY', YOUTUBE_API_KEY)

##### Custom Courses for EdX #####
if FEATURES.get('CUSTOM_COURSES_EDX'):
    INSTALLED_APPS += ['lms.djangoapps.ccx', 'openedx.core.djangoapps.ccxcon.apps.CCXConnectorConfig']
    MODULESTORE_FIELD_OVERRIDE_PROVIDERS += (
        'lms.djangoapps.ccx.overrides.CustomCoursesForEdxOverrideProvider',
    )

##### Individual Due Date Extensions #####
if FEATURES.get('INDIVIDUAL_DUE_DATES'):
    FIELD_OVERRIDE_PROVIDERS += (
        'lms.djangoapps.courseware.student_field_overrides.IndividualStudentOverrideProvider',
    )

##### Show Answer Override for Self-Paced Courses #####
FIELD_OVERRIDE_PROVIDERS += (
    'openedx.features.personalized_learner_schedules.show_answer.show_answer_field_override.ShowAnswerFieldOverride',
)

##### Self-Paced Course Due Dates #####
XBLOCK_FIELD_DATA_WRAPPERS += (
    'lms.djangoapps.courseware.field_overrides:OverrideModulestoreFieldData.wrap',
)

MODULESTORE_FIELD_OVERRIDE_PROVIDERS += (
    'lms.djangoapps.courseware.self_paced_overrides.SelfPacedDateOverrideProvider',
)

# PROFILE IMAGE CONFIG
PROFILE_IMAGE_DEFAULT_FILENAME = 'images/profiles/default'
PROFILE_IMAGE_SIZES_MAP = ENV_TOKENS.get(
    'PROFILE_IMAGE_SIZES_MAP',
    PROFILE_IMAGE_SIZES_MAP
)

##### Credit Provider Integration #####

CREDIT_PROVIDER_SECRET_KEYS = AUTH_TOKENS.get("CREDIT_PROVIDER_SECRET_KEYS", {})

##################### LTI Provider #####################
if FEATURES.get('ENABLE_LTI_PROVIDER'):
    INSTALLED_APPS.append('lms.djangoapps.lti_provider.apps.LtiProviderConfig')
    AUTHENTICATION_BACKENDS.append('lms.djangoapps.lti_provider.users.LtiBackend')

LTI_USER_EMAIL_DOMAIN = ENV_TOKENS.get('LTI_USER_EMAIL_DOMAIN', 'lti.example.com')

# For more info on this, see the notes in common.py
LTI_AGGREGATE_SCORE_PASSBACK_DELAY = ENV_TOKENS.get(
    'LTI_AGGREGATE_SCORE_PASSBACK_DELAY', LTI_AGGREGATE_SCORE_PASSBACK_DELAY
)

##################### Credit Provider help link ####################

#### JWT configuration ####
JWT_AUTH.update(ENV_TOKENS.get('JWT_AUTH', {}))
JWT_AUTH.update(AUTH_TOKENS.get('JWT_AUTH', {}))

# Offset for pk of courseware.StudentModuleHistoryExtended
STUDENTMODULEHISTORYEXTENDED_OFFSET = ENV_TOKENS.get(
    'STUDENTMODULEHISTORYEXTENDED_OFFSET', STUDENTMODULEHISTORYEXTENDED_OFFSET
)

################################ Settings for Credentials Service ################################

CREDENTIALS_GENERATION_ROUTING_KEY = ENV_TOKENS.get('CREDENTIALS_GENERATION_ROUTING_KEY', DEFAULT_PRIORITY_QUEUE)

# Queue to use for award program certificates
PROGRAM_CERTIFICATES_ROUTING_KEY = ENV_TOKENS.get('PROGRAM_CERTIFICATES_ROUTING_KEY', DEFAULT_PRIORITY_QUEUE)
SOFTWARE_SECURE_VERIFICATION_ROUTING_KEY = ENV_TOKENS.get(
    'SOFTWARE_SECURE_VERIFICATION_ROUTING_KEY',
    HIGH_PRIORITY_QUEUE
)

API_ACCESS_MANAGER_EMAIL = ENV_TOKENS.get('API_ACCESS_MANAGER_EMAIL')
API_ACCESS_FROM_EMAIL = ENV_TOKENS.get('API_ACCESS_FROM_EMAIL')

############## OPEN EDX ENTERPRISE SERVICE CONFIGURATION ######################
# The Open edX Enterprise service is currently hosted via the LMS container/process.
# However, for all intents and purposes this service is treated as a standalone IDA.
# These configuration settings are specific to the Enterprise service and you should
# not find references to them within the edx-platform project.

# Publicly-accessible enrollment URL, for use on the client side.
ENTERPRISE_PUBLIC_ENROLLMENT_API_URL = ENV_TOKENS.get(
    'ENTERPRISE_PUBLIC_ENROLLMENT_API_URL',
    (LMS_ROOT_URL or '') + LMS_ENROLLMENT_API_PATH
)

# Enrollment URL used on the server-side.
ENTERPRISE_ENROLLMENT_API_URL = ENV_TOKENS.get(
    'ENTERPRISE_ENROLLMENT_API_URL',
    (LMS_INTERNAL_ROOT_URL or '') + LMS_ENROLLMENT_API_PATH
)

# Enterprise logo image size limit in KB's
ENTERPRISE_CUSTOMER_LOGO_IMAGE_SIZE = ENV_TOKENS.get(
    'ENTERPRISE_CUSTOMER_LOGO_IMAGE_SIZE',
    ENTERPRISE_CUSTOMER_LOGO_IMAGE_SIZE
)

# Course enrollment modes to be hidden in the Enterprise enrollment page
# if the "Hide audit track" flag is enabled for an EnterpriseCustomer
ENTERPRISE_COURSE_ENROLLMENT_AUDIT_MODES = ENV_TOKENS.get(
    'ENTERPRISE_COURSE_ENROLLMENT_AUDIT_MODES',
    ENTERPRISE_COURSE_ENROLLMENT_AUDIT_MODES
)

# A support URL used on Enterprise landing pages for when a warning
# message goes off.
ENTERPRISE_SUPPORT_URL = ENV_TOKENS.get(
    'ENTERPRISE_SUPPORT_URL',
    ENTERPRISE_SUPPORT_URL
)

# A default dictionary to be used for filtering out enterprise customer catalog.
ENTERPRISE_CUSTOMER_CATALOG_DEFAULT_CONTENT_FILTER = ENV_TOKENS.get(
    'ENTERPRISE_CUSTOMER_CATALOG_DEFAULT_CONTENT_FILTER',
    ENTERPRISE_CUSTOMER_CATALOG_DEFAULT_CONTENT_FILTER
)
INTEGRATED_CHANNELS_API_CHUNK_TRANSMISSION_LIMIT = ENV_TOKENS.get(
    'INTEGRATED_CHANNELS_API_CHUNK_TRANSMISSION_LIMIT',
    INTEGRATED_CHANNELS_API_CHUNK_TRANSMISSION_LIMIT
)

############## ENTERPRISE SERVICE API CLIENT CONFIGURATION ######################
# The LMS communicates with the Enterprise service via the requests.Session() client
# The below environmental settings are utilized by the LMS when interacting with
# the service, and override the default parameters which are defined in common.py

DEFAULT_ENTERPRISE_API_URL = None
if LMS_INTERNAL_ROOT_URL is not None:
    DEFAULT_ENTERPRISE_API_URL = LMS_INTERNAL_ROOT_URL + '/enterprise/api/v1/'
ENTERPRISE_API_URL = ENV_TOKENS.get('ENTERPRISE_API_URL', DEFAULT_ENTERPRISE_API_URL)

DEFAULT_ENTERPRISE_CONSENT_API_URL = None
if LMS_INTERNAL_ROOT_URL is not None:
    DEFAULT_ENTERPRISE_CONSENT_API_URL = LMS_INTERNAL_ROOT_URL + '/consent/api/v1/'
ENTERPRISE_CONSENT_API_URL = ENV_TOKENS.get('ENTERPRISE_CONSENT_API_URL', DEFAULT_ENTERPRISE_CONSENT_API_URL)

ENTERPRISE_SERVICE_WORKER_USERNAME = ENV_TOKENS.get(
    'ENTERPRISE_SERVICE_WORKER_USERNAME',
    ENTERPRISE_SERVICE_WORKER_USERNAME
)
ENTERPRISE_API_CACHE_TIMEOUT = ENV_TOKENS.get(
    'ENTERPRISE_API_CACHE_TIMEOUT',
    ENTERPRISE_API_CACHE_TIMEOUT
)
ENTERPRISE_CATALOG_INTERNAL_ROOT_URL = ENV_TOKENS.get(
    'ENTERPRISE_CATALOG_INTERNAL_ROOT_URL',
    ENTERPRISE_CATALOG_INTERNAL_ROOT_URL
)

CHAT_COMPLETION_API = ENV_TOKENS.get('CHAT_COMPLETION_API', '')
CHAT_COMPLETION_API_KEY = ENV_TOKENS.get('CHAT_COMPLETION_API_KEY', '')
LEARNER_ENGAGEMENT_PROMPT_FOR_ACTIVE_CONTRACT = ENV_TOKENS.get('LEARNER_ENGAGEMENT_PROMPT_FOR_ACTIVE_CONTRACT', '')
LEARNER_ENGAGEMENT_PROMPT_FOR_NON_ACTIVE_CONTRACT = ENV_TOKENS.get(
    'LEARNER_ENGAGEMENT_PROMPT_FOR_NON_ACTIVE_CONTRACT',
    ''
)
LEARNER_PROGRESS_PROMPT_FOR_ACTIVE_CONTRACT = ENV_TOKENS.get('LEARNER_PROGRESS_PROMPT_FOR_ACTIVE_CONTRACT', '')
LEARNER_PROGRESS_PROMPT_FOR_NON_ACTIVE_CONTRACT = ENV_TOKENS.get('LEARNER_PROGRESS_PROMPT_FOR_NON_ACTIVE_CONTRACT', '')

############## ENTERPRISE SERVICE LMS CONFIGURATION ##################################
# The LMS has some features embedded that are related to the Enterprise service, but
# which are not provided by the Enterprise service. These settings override the
# base values for the parameters as defined in common.py

ENTERPRISE_PLATFORM_WELCOME_TEMPLATE = ENV_TOKENS.get(
    'ENTERPRISE_PLATFORM_WELCOME_TEMPLATE',
    ENTERPRISE_PLATFORM_WELCOME_TEMPLATE
)
ENTERPRISE_SPECIFIC_BRANDED_WELCOME_TEMPLATE = ENV_TOKENS.get(
    'ENTERPRISE_SPECIFIC_BRANDED_WELCOME_TEMPLATE',
    ENTERPRISE_SPECIFIC_BRANDED_WELCOME_TEMPLATE
)
ENTERPRISE_TAGLINE = ENV_TOKENS.get(
    'ENTERPRISE_TAGLINE',
    ENTERPRISE_TAGLINE
)
ENTERPRISE_EXCLUDED_REGISTRATION_FIELDS = set(
    ENV_TOKENS.get(
        'ENTERPRISE_EXCLUDED_REGISTRATION_FIELDS',
        ENTERPRISE_EXCLUDED_REGISTRATION_FIELDS
    )
)
BASE_COOKIE_DOMAIN = ENV_TOKENS.get(
    'BASE_COOKIE_DOMAIN',
    BASE_COOKIE_DOMAIN
)
SYSTEM_TO_FEATURE_ROLE_MAPPING = ENV_TOKENS.get(
    'SYSTEM_TO_FEATURE_ROLE_MAPPING',
    SYSTEM_TO_FEATURE_ROLE_MAPPING
)

# Add an ICP license for serving content in China if your organization is registered to do so
ICP_LICENSE = ENV_TOKENS.get('ICP_LICENSE', None)
ICP_LICENSE_INFO = ENV_TOKENS.get('ICP_LICENSE_INFO', {})

# How long to cache OpenAPI schemas and UI, in seconds.
OPENAPI_CACHE_TIMEOUT = ENV_TOKENS.get('OPENAPI_CACHE_TIMEOUT', 60 * 60)

########################## Parental controls config  #######################

# The age at which a learner no longer requires parental consent, or None
# if parental consent is never required.
PARENTAL_CONSENT_AGE_LIMIT = ENV_TOKENS.get(
    'PARENTAL_CONSENT_AGE_LIMIT',
    PARENTAL_CONSENT_AGE_LIMIT
)

########################## Extra middleware classes  #######################

# Allow extra middleware classes to be added to the app through configuration.
MIDDLEWARE.extend(ENV_TOKENS.get('EXTRA_MIDDLEWARE_CLASSES', []))

################# Settings for the maintenance banner #################
MAINTENANCE_BANNER_TEXT = ENV_TOKENS.get('MAINTENANCE_BANNER_TEXT', None)

########################## limiting dashboard courses ######################
DASHBOARD_COURSE_LIMIT = ENV_TOKENS.get('DASHBOARD_COURSE_LIMIT', None)

######################## Setting for content libraries ########################
MAX_BLOCKS_PER_CONTENT_LIBRARY = ENV_TOKENS.get('MAX_BLOCKS_PER_CONTENT_LIBRARY', MAX_BLOCKS_PER_CONTENT_LIBRARY)

########################## Derive Any Derived Settings  #######################

derive_settings(__name__)

############################### Plugin Settings ###############################

# This is at the bottom because it is going to load more settings after base settings are loaded

# Load production.py in plugins
add_plugins(__name__, ProjectType.LMS, SettingsType.PRODUCTION)

############## Settings for Completion API #########################

# Once a user has watched this percentage of a video, mark it as complete:
# (0.0 = 0%, 1.0 = 100%)
COMPLETION_VIDEO_COMPLETE_PERCENTAGE = ENV_TOKENS.get('COMPLETION_VIDEO_COMPLETE_PERCENTAGE',
                                                      COMPLETION_VIDEO_COMPLETE_PERCENTAGE)
COMPLETION_BY_VIEWING_DELAY_MS = ENV_TOKENS.get('COMPLETION_BY_VIEWING_DELAY_MS',
                                                COMPLETION_BY_VIEWING_DELAY_MS)

################# Settings for brand logos. #################
LOGO_URL = ENV_TOKENS.get('LOGO_URL', LOGO_URL)
LOGO_URL_PNG = ENV_TOKENS.get('LOGO_URL_PNG', LOGO_URL_PNG)
LOGO_TRADEMARK_URL = ENV_TOKENS.get('LOGO_TRADEMARK_URL', LOGO_TRADEMARK_URL)
FAVICON_URL = ENV_TOKENS.get('FAVICON_URL', FAVICON_URL)

######################## CELERY ROUTING ########################

# Defines alternate environment tasks, as a dict of form { task_name: alternate_queue }
ALTERNATE_ENV_TASKS = {}

# Defines the task -> alternate worker queue to be used when routing.
EXPLICIT_QUEUES = {
    'openedx.core.djangoapps.content.course_overviews.tasks.async_course_overview_update': {
        'queue': GRADES_DOWNLOAD_ROUTING_KEY},
    'lms.djangoapps.bulk_email.tasks.send_course_email': {
        'queue': BULK_EMAIL_ROUTING_KEY},
    'openedx.core.djangoapps.heartbeat.tasks.sample_task': {
        'queue': HEARTBEAT_CELERY_ROUTING_KEY},
    'lms.djangoapps.instructor_task.tasks.calculate_grades_csv': {
        'queue': GRADES_DOWNLOAD_ROUTING_KEY},
    'lms.djangoapps.instructor_task.tasks.calculate_problem_grade_report': {
        'queue': GRADES_DOWNLOAD_ROUTING_KEY},
    'lms.djangoapps.instructor_task.tasks.generate_certificates': {
        'queue': GRADES_DOWNLOAD_ROUTING_KEY},
    'lms.djangoapps.verify_student.tasks.send_verification_status_email': {
        'queue': ACE_ROUTING_KEY},
    'lms.djangoapps.verify_student.tasks.send_ace_message': {
        'queue': ACE_ROUTING_KEY},
    'lms.djangoapps.verify_student.tasks.send_request_to_ss_for_user': {
        'queue': SOFTWARE_SECURE_VERIFICATION_ROUTING_KEY},
    'openedx.core.djangoapps.schedules.tasks._recurring_nudge_schedule_send': {
        'queue': ACE_ROUTING_KEY},
    'openedx.core.djangoapps.schedules.tasks._upgrade_reminder_schedule_send': {
        'queue': ACE_ROUTING_KEY},
    'openedx.core.djangoapps.schedules.tasks._course_update_schedule_send': {
        'queue': ACE_ROUTING_KEY},
    'openedx.core.djangoapps.schedules.tasks.v1.tasks.send_grade_to_credentials': {
        'queue': CREDENTIALS_GENERATION_ROUTING_KEY},
    'common.djangoapps.entitlements.tasks.expire_old_entitlements': {
        'queue': ENTITLEMENTS_EXPIRATION_ROUTING_KEY},
    'lms.djangoapps.grades.tasks.recalculate_course_and_subsection_grades_for_user': {
        'queue': POLICY_CHANGE_GRADES_ROUTING_KEY},
    'lms.djangoapps.grades.tasks.recalculate_subsection_grade_v3': {
        'queue': SINGLE_LEARNER_COURSE_REGRADE_ROUTING_KEY},
    'openedx.core.djangoapps.programs.tasks.award_program_certificates': {
        'queue': PROGRAM_CERTIFICATES_ROUTING_KEY},
    'openedx.core.djangoapps.programs.tasks.revoke_program_certificates': {
        'queue': PROGRAM_CERTIFICATES_ROUTING_KEY},
    'openedx.core.djangoapps.programs.tasks.update_certificate_available_date_on_course_update': {
        'queue': PROGRAM_CERTIFICATES_ROUTING_KEY},
    'openedx.core.djangoapps.programs.tasks.award_course_certificate': {
        'queue': PROGRAM_CERTIFICATES_ROUTING_KEY},
    'openassessment.workflow.tasks.update_workflows_for_all_blocked_submissions_task': {
        'queue': ORA_WORKFLOW_UPDATE_ROUTING_KEY},
    'openassessment.workflow.tasks.update_workflows_for_course_task': {
        'queue': ORA_WORKFLOW_UPDATE_ROUTING_KEY},
    'openassessment.workflow.tasks.update_workflows_for_ora_block_task': {
        'queue': ORA_WORKFLOW_UPDATE_ROUTING_KEY},
    'openassessment.workflow.tasks.update_workflow_for_submission_task': {
        'queue': ORA_WORKFLOW_UPDATE_ROUTING_KEY},

}

LOGO_IMAGE_EXTRA_TEXT = ENV_TOKENS.get('LOGO_IMAGE_EXTRA_TEXT', '')

############## XBlock extra mixins ############################
XBLOCK_MIXINS += tuple(XBLOCK_EXTRA_MIXINS)

############## Settings for course import olx validation ############################
COURSE_OLX_VALIDATION_STAGE = ENV_TOKENS.get('COURSE_OLX_VALIDATION_STAGE', COURSE_OLX_VALIDATION_STAGE)
COURSE_OLX_VALIDATION_IGNORE_LIST = ENV_TOKENS.get(
    'COURSE_OLX_VALIDATION_IGNORE_LIST',
    COURSE_OLX_VALIDATION_IGNORE_LIST
)

################# show account activate cta after register ########################
SHOW_ACCOUNT_ACTIVATION_CTA = ENV_TOKENS.get('SHOW_ACCOUNT_ACTIVATION_CTA', SHOW_ACCOUNT_ACTIVATION_CTA)

################# Discussions micro frontend URL ########################
DISCUSSIONS_MICROFRONTEND_URL = ENV_TOKENS.get('DISCUSSIONS_MICROFRONTEND_URL', DISCUSSIONS_MICROFRONTEND_URL)

################### Discussions micro frontend Feedback URL###################
DISCUSSIONS_MFE_FEEDBACK_URL = ENV_TOKENS.get('DISCUSSIONS_MFE_FEEDBACK_URL', DISCUSSIONS_MFE_FEEDBACK_URL)

############################ AI_TRANSLATIONS URL ##################################
AI_TRANSLATIONS_API_URL = ENV_TOKENS.get('AI_TRANSLATIONS_API_URL', AI_TRANSLATIONS_API_URL)

############## DRF overrides ##############
REST_FRAMEWORK.update(ENV_TOKENS.get('REST_FRAMEWORK', {}))

############################# CELERY ############################
CELERY_IMPORTS.extend(ENV_TOKENS.get('CELERY_EXTRA_IMPORTS', []))

# keys for  big blue button live provider
COURSE_LIVE_GLOBAL_CREDENTIALS["BIG_BLUE_BUTTON"] = {
    "KEY": ENV_TOKENS.get('BIG_BLUE_BUTTON_GLOBAL_KEY', None),
    "SECRET": ENV_TOKENS.get('BIG_BLUE_BUTTON_GLOBAL_SECRET', None),
    "URL": ENV_TOKENS.get('BIG_BLUE_BUTTON_GLOBAL_URL', None),
}

AVAILABLE_DISCUSSION_TOURS = ENV_TOKENS.get('AVAILABLE_DISCUSSION_TOURS', [])

############## NOTIFICATIONS EXPIRY ##############
NOTIFICATIONS_EXPIRY = ENV_TOKENS.get('NOTIFICATIONS_EXPIRY', NOTIFICATIONS_EXPIRY)

############## Event bus producer ##############
EVENT_BUS_PRODUCER_CONFIG = merge_producer_configs(EVENT_BUS_PRODUCER_CONFIG,
                                                   ENV_TOKENS.get('EVENT_BUS_PRODUCER_CONFIG', {}))
BEAMER_PRODUCT_ID = ENV_TOKENS.get('BEAMER_PRODUCT_ID', BEAMER_PRODUCT_ID)

# .. setting_name: DISABLED_COUNTRIES
# .. setting_default: []
# .. setting_description: List of country codes that should be disabled
# .. for now it wil impact country listing in auth flow and user profile.
# .. eg ['US', 'CA']
DISABLED_COUNTRIES = ENV_TOKENS.get('DISABLED_COUNTRIES', [])
