"""
This is the default template for our main set of AWS servers.
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=wildcard-import, unused-wildcard-import


import codecs
import copy
import os
import warnings
import yaml

import django
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse_lazy
from edx_django_utils.plugins import add_plugins
from openedx_events.event_bus import merge_producer_configs
from path import Path as path

from openedx.core.djangoapps.plugins.constants import ProjectType, SettingsType

from .common import *

from openedx.core.lib.derived import derive_settings  # lint-amnesty, pylint: disable=wrong-import-order
from openedx.core.lib.logsettings import get_logger_config  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.modulestore_settings import convert_module_store_setting_if_needed  # lint-amnesty, pylint: disable=wrong-import-order


def get_env_setting(setting):
    """ Get the environment setting or return exception """
    try:
        return os.environ[setting]
    except KeyError:
        error_msg = "Set the %s env variable" % setting
        raise ImproperlyConfigured(error_msg)  # lint-amnesty, pylint: disable=raise-missing-from

############### ALWAYS THE SAME ################################

DEBUG = False

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

# IMPORTANT: With this enabled, the server must always be behind a proxy that
# strips the header HTTP_X_FORWARDED_PROTO from client requests. Otherwise,
# a user can fool our server into thinking it was an https connection.
# See
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
# for other warnings.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
############### END ALWAYS THE SAME ################################

# A file path to a YAML file from which to load all the configuration for the edx platform
try:
    CONFIG_FILE = get_env_setting('CMS_CFG')
except ImproperlyConfigured:
    CONFIG_FILE = get_env_setting('STUDIO_CFG')
    warnings.warn(
        "STUDIO_CFG environment variable is deprecated. Use CMS_CFG instead.",
        DeprecationWarning,
        stacklevel=2,
    )

with codecs.open(CONFIG_FILE, encoding='utf-8') as f:
    __config__ = yaml.safe_load(f)

    # ENV_TOKENS and AUTH_TOKENS are included for reverse compatability.
    # Removing them may break plugins that rely on them.
    ENV_TOKENS = __config__
    AUTH_TOKENS = __config__

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
        'MKTG_URL_OVERRIDES',
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

# Allow env to configure celery result backend with default set to django-cache
CELERY_RESULT_BACKEND = ENV_TOKENS.get('CELERY_RESULT_BACKEND', 'django-cache')

# When the broker is behind an ELB, use a heartbeat to refresh the
# connection and to detect if it has been dropped.
BROKER_HEARTBEAT = ENV_TOKENS.get('BROKER_HEARTBEAT', 60.0)
BROKER_HEARTBEAT_CHECKRATE = ENV_TOKENS.get('BROKER_HEARTBEAT_CHECKRATE', 2)

# Each worker should only fetch one message at a time
CELERYD_PREFETCH_MULTIPLIER = 1

CELERY_ROUTES = "openedx.core.lib.celery.routers.route_task"

# STATIC_URL_BASE specifies the base url to use for static files
STATIC_URL_BASE = ENV_TOKENS.get('STATIC_URL_BASE', None)
if STATIC_URL_BASE:
    STATIC_URL = STATIC_URL_BASE
    if not STATIC_URL.endswith("/"):
        STATIC_URL += "/"
    STATIC_URL += 'studio/'

DEFAULT_COURSE_VISIBILITY_IN_CATALOG = ENV_TOKENS.get(
    'DEFAULT_COURSE_VISIBILITY_IN_CATALOG',
    DEFAULT_COURSE_VISIBILITY_IN_CATALOG
)

# DEFAULT_MOBILE_AVAILABLE specifies if the course is available for mobile by default
DEFAULT_MOBILE_AVAILABLE = ENV_TOKENS.get(
    'DEFAULT_MOBILE_AVAILABLE',
    DEFAULT_MOBILE_AVAILABLE
)

# How long to cache OpenAPI schemas and UI, in seconds.
OPENAPI_CACHE_TIMEOUT = ENV_TOKENS.get('OPENAPI_CACHE_TIMEOUT', 60 * 60)

# STATIC_ROOT specifies the directory where static files are
# collected

STATIC_ROOT_BASE = ENV_TOKENS.get('STATIC_ROOT_BASE', None)
if STATIC_ROOT_BASE:
    STATIC_ROOT = path(STATIC_ROOT_BASE) / 'studio'
    WEBPACK_LOADER['DEFAULT']['STATS_FILE'] = STATIC_ROOT / "webpack-stats.json"
    WEBPACK_LOADER['WORKERS']['STATS_FILE'] = STATIC_ROOT / "webpack-worker-stats.json"

DATA_DIR = path(ENV_TOKENS.get('DATA_DIR', DATA_DIR))
EMAIL_FILE_PATH = ENV_TOKENS.get('EMAIL_FILE_PATH', DATA_DIR / "emails" / "studio")


# CMS_BASE: Public domain name of Studio (should be resolvable from the end-user's browser)
CMS_BASE = ENV_TOKENS.get('CMS_BASE')
LMS_BASE = ENV_TOKENS.get('LMS_BASE')
LMS_ROOT_URL = ENV_TOKENS.get('LMS_ROOT_URL')
LMS_INTERNAL_ROOT_URL = ENV_TOKENS.get('LMS_INTERNAL_ROOT_URL', LMS_ROOT_URL)
ENTERPRISE_API_URL = ENV_TOKENS.get('ENTERPRISE_API_URL', LMS_INTERNAL_ROOT_URL + '/enterprise/api/v1/')
ENTERPRISE_CONSENT_API_URL = ENV_TOKENS.get('ENTERPRISE_CONSENT_API_URL', LMS_INTERNAL_ROOT_URL + '/consent/api/v1/')
AUTHORING_API_URL = ENV_TOKENS.get('AUTHORING_API_URL', '')
# Note that FEATURES['PREVIEW_LMS_BASE'] gets read in from the environment file.

CHAT_COMPLETION_API = ENV_TOKENS.get('CHAT_COMPLETION_API', '')
CHAT_COMPLETION_API_KEY = ENV_TOKENS.get('CHAT_COMPLETION_API_KEY', '')
LEARNER_ENGAGEMENT_PROMPT_FOR_ACTIVE_CONTRACT = ENV_TOKENS.get('LEARNER_ENGAGEMENT_PROMPT_FOR_ACTIVE_CONTRACT', '')
LEARNER_ENGAGEMENT_PROMPT_FOR_NON_ACTIVE_CONTRACT = ENV_TOKENS.get(
    'LEARNER_ENGAGEMENT_PROMPT_FOR_NON_ACTIVE_CONTRACT',
    ''
)
LEARNER_PROGRESS_PROMPT_FOR_ACTIVE_CONTRACT = ENV_TOKENS.get('LEARNER_PROGRESS_PROMPT_FOR_ACTIVE_CONTRACT', '')
LEARNER_PROGRESS_PROMPT_FOR_NON_ACTIVE_CONTRACT = ENV_TOKENS.get('LEARNER_PROGRESS_PROMPT_FOR_NON_ACTIVE_CONTRACT', '')

# List of logout URIs for each IDA that the learner should be logged out of when they logout of
# Studio. Only applies to IDA for which the social auth flow uses DOT (Django OAuth Toolkit).
IDA_LOGOUT_URI_LIST = ENV_TOKENS.get('IDA_LOGOUT_URI_LIST', [])

SITE_NAME = ENV_TOKENS.get('SITE_NAME', SITE_NAME)

ALLOWED_HOSTS = [
    # TODO: bbeggs remove this before prod, temp fix to get load testing running
    "*",
    CMS_BASE,
]

LOG_DIR = ENV_TOKENS.get('LOG_DIR', LOG_DIR)

CACHES = ENV_TOKENS.get('CACHES', CACHES)
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
STATICFILES_STORAGE = os.environ.get('STATICFILES_STORAGE', ENV_TOKENS.get('STATICFILES_STORAGE', STATICFILES_STORAGE))

# Load all AWS_ prefixed variables to allow an S3Boto3Storage to be configured
_locals = locals()
for key, value in ENV_TOKENS.items():
    if key.startswith('AWS_'):
        _locals[key] = value

SESSION_COOKIE_DOMAIN = ENV_TOKENS.get('SESSION_COOKIE_DOMAIN')
SESSION_COOKIE_HTTPONLY = ENV_TOKENS.get('SESSION_COOKIE_HTTPONLY', True)

REGISTRATION_EMAIL_PATTERNS_ALLOWED = ENV_TOKENS.get('REGISTRATION_EMAIL_PATTERNS_ALLOWED')

# allow for environments to specify what cookie name our login subsystem should use
# this is to fix a bug regarding simultaneous logins between edx.org and edge.edx.org which can
# happen with some browsers (e.g. Firefox)
if ENV_TOKENS.get('SESSION_COOKIE_NAME', None):
    # NOTE, there's a bug in Django (http://bugs.python.org/issue18012) which necessitates this being a str()
    SESSION_COOKIE_NAME = str(ENV_TOKENS.get('SESSION_COOKIE_NAME'))

# This is the domain that is used to set shared cookies between various sub-domains.
# By default, it's set to the same thing as the SESSION_COOKIE_DOMAIN, but we want to make it overrideable.
SHARED_COOKIE_DOMAIN = ENV_TOKENS.get('SHARED_COOKIE_DOMAIN', SESSION_COOKIE_DOMAIN)

# Determines whether the CSRF token can be transported on
# unencrypted channels. It is set to False here for backward compatibility,
# but it is highly recommended that this is True for environments accessed
# by end users.
CSRF_COOKIE_SECURE = ENV_TOKENS.get('CSRF_COOKIE_SECURE', False)

# values are already updated above with default CSRF_TRUSTED_ORIGINS values but in
# case of new django version these values will override.
if django.VERSION[0] >= 4:  # for greater than django 3.2 use schemes.
    CSRF_TRUSTED_ORIGINS = ENV_TOKENS.get('CSRF_TRUSTED_ORIGINS_WITH_SCHEME', [])

#Email overrides
MKTG_URL_LINK_MAP.update(ENV_TOKENS.get('MKTG_URL_LINK_MAP', {}))
MKTG_URL_OVERRIDES.update(ENV_TOKENS.get('MKTG_URL_OVERRIDES', MKTG_URL_OVERRIDES))

for name, value in ENV_TOKENS.get("CODE_JAIL", {}).items():
    oldvalue = CODE_JAIL.get(name)
    if isinstance(oldvalue, dict):
        for subname, subvalue in value.items():
            oldvalue[subname] = subvalue
    else:
        CODE_JAIL[name] = value

COURSES_WITH_UNSAFE_CODE = ENV_TOKENS.get("COURSES_WITH_UNSAFE_CODE", [])

# COMPREHENSIVE_THEME_LOCALE_PATHS contain the paths to themes locale directories e.g.
# "COMPREHENSIVE_THEME_LOCALE_PATHS" : [
#        "/edx/src/edx-themes/conf/locale"
#    ],
COMPREHENSIVE_THEME_LOCALE_PATHS = ENV_TOKENS.get('COMPREHENSIVE_THEME_LOCALE_PATHS', [])

# PREPEND_LOCALE_PATHS contain the paths to locale directories to load first e.g.
# "PREPEND_LOCALE_PATHS" : [
#        "/edx/my-locale/"
#    ],
PREPEND_LOCALE_PATHS = ENV_TOKENS.get('PREPEND_LOCALE_PATHS', [])

#Timezone overrides
TIME_ZONE = ENV_TOKENS.get('CELERY_TIMEZONE', CELERY_TIMEZONE)

##### REGISTRATION RATE LIMIT SETTINGS #####
REGISTRATION_VALIDATION_RATELIMIT = ENV_TOKENS.get(
    'REGISTRATION_VALIDATION_RATELIMIT', REGISTRATION_VALIDATION_RATELIMIT
)
REGISTRATION_RATELIMIT = ENV_TOKENS.get('REGISTRATION_RATELIMIT', REGISTRATION_RATELIMIT)

# Push to LMS overrides
GIT_REPO_EXPORT_DIR = ENV_TOKENS.get('GIT_REPO_EXPORT_DIR', '/edx/var/edxapp/export_course_repos')

ENV_FEATURES = ENV_TOKENS.get('FEATURES', {})
for feature, value in ENV_FEATURES.items():
    FEATURES[feature] = value

# Additional installed apps
for app in ENV_TOKENS.get('ADDL_INSTALLED_APPS', []):
    INSTALLED_APPS.append(app)

LOGGING = get_logger_config(LOG_DIR,
                            logging_env=ENV_TOKENS.get('LOGGING_ENV', LOGGING_ENV),
                            service_variant=SERVICE_VARIANT)

# The following variables use (or) instead of the default value inside (get). This is to enforce using the Lazy Text
# values when the varibale is an empty string. Therefore, setting these variable as empty text in related
# json files will make the system reads thier values from django translation files
PLATFORM_NAME = ENV_TOKENS.get('PLATFORM_NAME') or PLATFORM_NAME
PLATFORM_DESCRIPTION = ENV_TOKENS.get('PLATFORM_DESCRIPTION') or PLATFORM_DESCRIPTION
STUDIO_NAME = ENV_TOKENS.get('STUDIO_NAME') or STUDIO_NAME
STUDIO_SHORT_NAME = ENV_TOKENS.get('STUDIO_SHORT_NAME') or STUDIO_SHORT_NAME

# Event Tracking
if "TRACKING_IGNORE_URL_PATTERNS" in ENV_TOKENS:
    TRACKING_IGNORE_URL_PATTERNS = ENV_TOKENS.get("TRACKING_IGNORE_URL_PATTERNS")

# Heartbeat
HEARTBEAT_CELERY_ROUTING_KEY = ENV_TOKENS.get('HEARTBEAT_CELERY_ROUTING_KEY', HEARTBEAT_CELERY_ROUTING_KEY)

# Sometimes, OAuth2 clients want the user to redirect back to their site after logout. But to determine if the given
# redirect URL/path is safe for redirection, the following variable is used by edX.
LOGIN_REDIRECT_WHITELIST = ENV_TOKENS.get(
    'LOGIN_REDIRECT_WHITELIST',
    LOGIN_REDIRECT_WHITELIST
)
LOGIN_REDIRECT_WHITELIST.extend([reverse_lazy('home')])

############### XBlock filesystem field config ##########
if 'DJFS' in AUTH_TOKENS and AUTH_TOKENS['DJFS'] is not None:
    DJFS = AUTH_TOKENS['DJFS']
    if 'url_root' in DJFS:
        DJFS['url_root'] = DJFS['url_root'].format(platform_revision=EDX_PLATFORM_REVISION)


AWS_SES_REGION_NAME = ENV_TOKENS.get('AWS_SES_REGION_NAME', 'us-east-1')
AWS_SES_REGION_ENDPOINT = ENV_TOKENS.get('AWS_SES_REGION_ENDPOINT', 'email.us-east-1.amazonaws.com')

# Note that this is the Studio key for Segment. There is a separate key for the LMS.
CMS_SEGMENT_KEY = AUTH_TOKENS.get('SEGMENT_KEY')

SECRET_KEY = AUTH_TOKENS['SECRET_KEY']

AWS_ACCESS_KEY_ID = AUTH_TOKENS.get("AWS_ACCESS_KEY_ID", AWS_ACCESS_KEY_ID)
if AWS_ACCESS_KEY_ID == "":
    AWS_ACCESS_KEY_ID = None

AWS_SECRET_ACCESS_KEY = AUTH_TOKENS.get("AWS_SECRET_ACCESS_KEY", AWS_SECRET_ACCESS_KEY)
if AWS_SECRET_ACCESS_KEY == "":
    AWS_SECRET_ACCESS_KEY = None

AWS_STORAGE_BUCKET_NAME = AUTH_TOKENS.get('AWS_STORAGE_BUCKET_NAME', 'edxuploads')

# Disabling querystring auth instructs Boto to exclude the querystring parameters (e.g. signature, access key) it
# normally appends to every returned URL.
AWS_QUERYSTRING_AUTH = AUTH_TOKENS.get('AWS_QUERYSTRING_AUTH', True)

AWS_DEFAULT_ACL = 'private'
AWS_BUCKET_ACL = AWS_DEFAULT_ACL
# The number of seconds that a generated URL is valid for.
AWS_QUERYSTRING_EXPIRE = 7 * 24 * 60 * 60  # 7 days
AWS_S3_CUSTOM_DOMAIN = AUTH_TOKENS.get('AWS_S3_CUSTOM_DOMAIN', 'edxuploads.s3.amazonaws.com')

if AUTH_TOKENS.get('DEFAULT_FILE_STORAGE'):
    DEFAULT_FILE_STORAGE = AUTH_TOKENS.get('DEFAULT_FILE_STORAGE')
elif AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
else:
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

COURSE_IMPORT_EXPORT_BUCKET = ENV_TOKENS.get('COURSE_IMPORT_EXPORT_BUCKET', '')

if COURSE_IMPORT_EXPORT_BUCKET:
    COURSE_IMPORT_EXPORT_STORAGE = 'cms.djangoapps.contentstore.storage.ImportExportS3Storage'
else:
    COURSE_IMPORT_EXPORT_STORAGE = DEFAULT_FILE_STORAGE

USER_TASKS_ARTIFACT_STORAGE = COURSE_IMPORT_EXPORT_STORAGE

COURSE_METADATA_EXPORT_BUCKET = ENV_TOKENS.get('COURSE_METADATA_EXPORT_BUCKET', '')

if COURSE_METADATA_EXPORT_BUCKET:
    COURSE_METADATA_EXPORT_STORAGE = 'cms.djangoapps.export_course_metadata.storage.CourseMetadataExportS3Storage'
else:
    COURSE_METADATA_EXPORT_STORAGE = DEFAULT_FILE_STORAGE

DATABASES = AUTH_TOKENS.get('DATABASES', DATABASES)

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

MODULESTORE = convert_module_store_setting_if_needed(AUTH_TOKENS.get('MODULESTORE', MODULESTORE))

MODULESTORE_FIELD_OVERRIDE_PROVIDERS = ENV_TOKENS.get(
    'MODULESTORE_FIELD_OVERRIDE_PROVIDERS',
    MODULESTORE_FIELD_OVERRIDE_PROVIDERS
)

XBLOCK_FIELD_DATA_WRAPPERS = ENV_TOKENS.get(
    'XBLOCK_FIELD_DATA_WRAPPERS',
    XBLOCK_FIELD_DATA_WRAPPERS
)

CONTENTSTORE = AUTH_TOKENS.get('CONTENTSTORE', CONTENTSTORE)
DOC_STORE_CONFIG = AUTH_TOKENS.get('DOC_STORE_CONFIG', DOC_STORE_CONFIG)

# Celery Broker
CELERY_ALWAYS_EAGER = ENV_TOKENS.get("CELERY_ALWAYS_EAGER", False)
CELERY_BROKER_TRANSPORT = ENV_TOKENS.get("CELERY_BROKER_TRANSPORT", "")
CELERY_BROKER_HOSTNAME = ENV_TOKENS.get("CELERY_BROKER_HOSTNAME", "")
CELERY_BROKER_VHOST = ENV_TOKENS.get("CELERY_BROKER_VHOST", "")
CELERY_BROKER_USER = AUTH_TOKENS.get("CELERY_BROKER_USER", "")
CELERY_BROKER_PASSWORD = AUTH_TOKENS.get("CELERY_BROKER_PASSWORD", "")
CLEAR_REQUEST_CACHE_ON_TASK_COMPLETION = ENV_TOKENS.get("CLEAR_REQUEST_CACHE_ON_TASK_COMPLETION", True)

BROKER_URL = "{}://{}:{}@{}/{}".format(CELERY_BROKER_TRANSPORT,
                                       CELERY_BROKER_USER,
                                       CELERY_BROKER_PASSWORD,
                                       CELERY_BROKER_HOSTNAME,
                                       CELERY_BROKER_VHOST)
BROKER_USE_SSL = ENV_TOKENS.get('CELERY_BROKER_USE_SSL', False)

try:
    BROKER_TRANSPORT_OPTIONS = {
        'fanout_patterns': True,
        'fanout_prefix': True,
        **ENV_TOKENS.get('CELERY_BROKER_TRANSPORT_OPTIONS', {})
    }
except TypeError as exc:
    raise ImproperlyConfigured('CELERY_BROKER_TRANSPORT_OPTIONS must be a dict') from exc

# Message expiry time in seconds
CELERY_EVENT_QUEUE_TTL = ENV_TOKENS.get('CELERY_EVENT_QUEUE_TTL', None)

# Allow CELERY_QUEUES to be overwritten by ENV_TOKENS,
ENV_CELERY_QUEUES = ENV_TOKENS.get('CELERY_QUEUES', None)
if ENV_CELERY_QUEUES:
    CELERY_QUEUES = {queue: {} for queue in ENV_CELERY_QUEUES}

# Then add alternate environment queues
ALTERNATE_QUEUE_ENVS = ENV_TOKENS.get('ALTERNATE_WORKER_QUEUES', '').split()
ALTERNATE_QUEUES = [
    DEFAULT_PRIORITY_QUEUE.replace(QUEUE_VARIANT, alternate + '.')
    for alternate in ALTERNATE_QUEUE_ENVS
]

CELERY_QUEUES.update(
    {
        alternate: {}
        for alternate in ALTERNATE_QUEUES
        if alternate not in list(CELERY_QUEUES.keys())
    }
)

# Queue to use for updating grades due to grading policy change
POLICY_CHANGE_GRADES_ROUTING_KEY = ENV_TOKENS.get('POLICY_CHANGE_GRADES_ROUTING_KEY', DEFAULT_PRIORITY_QUEUE)

# Queue to use for individual learner course regrades
SINGLE_LEARNER_COURSE_REGRADE_ROUTING_KEY = ENV_TOKENS.get(
    'SINGLE_LEARNER_COURSE_REGRADE_ROUTING_KEY',
    DEFAULT_PRIORITY_QUEUE
)

SOFTWARE_SECURE_VERIFICATION_ROUTING_KEY = ENV_TOKENS.get(
    'SOFTWARE_SECURE_VERIFICATION_ROUTING_KEY',
    HIGH_PRIORITY_QUEUE
)

# Event tracking
TRACKING_BACKENDS.update(AUTH_TOKENS.get("TRACKING_BACKENDS", {}))
EVENT_TRACKING_BACKENDS['tracking_logs']['OPTIONS']['backends'].update(AUTH_TOKENS.get("EVENT_TRACKING_BACKENDS", {}))
EVENT_TRACKING_BACKENDS['segmentio']['OPTIONS']['processors'][0]['OPTIONS']['whitelist'].extend(
    AUTH_TOKENS.get("EVENT_TRACKING_SEGMENTIO_EMIT_WHITELIST", []))

##### ACCOUNT LOCKOUT DEFAULT PARAMETERS #####
MAX_FAILED_LOGIN_ATTEMPTS_ALLOWED = ENV_TOKENS.get(
    "MAX_FAILED_LOGIN_ATTEMPTS_ALLOWED", MAX_FAILED_LOGIN_ATTEMPTS_ALLOWED
)

MAX_FAILED_LOGIN_ATTEMPTS_LOCKOUT_PERIOD_SECS = ENV_TOKENS.get(
    "MAX_FAILED_LOGIN_ATTEMPTS_LOCKOUT_PERIOD_SECS", MAX_FAILED_LOGIN_ATTEMPTS_LOCKOUT_PERIOD_SECS
)

#### PASSWORD POLICY SETTINGS #####
AUTH_PASSWORD_VALIDATORS = ENV_TOKENS.get("AUTH_PASSWORD_VALIDATORS", AUTH_PASSWORD_VALIDATORS)

### INACTIVITY SETTINGS ####
SESSION_INACTIVITY_TIMEOUT_IN_SECONDS = AUTH_TOKENS.get("SESSION_INACTIVITY_TIMEOUT_IN_SECONDS")

################ PUSH NOTIFICATIONS ###############
PARSE_KEYS = AUTH_TOKENS.get("PARSE_KEYS", {})


# Video Caching. Pairing country codes with CDN URLs.
# Example: {'CN': 'http://api.xuetangx.com/edx/video?s3_url='}
VIDEO_CDN_URL = ENV_TOKENS.get('VIDEO_CDN_URL', {})

if FEATURES['ENABLE_COURSEWARE_INDEX'] or FEATURES['ENABLE_LIBRARY_INDEX']:
    # Use ElasticSearch for the search engine
    SEARCH_ENGINE = "search.elastic.ElasticSearchEngine"

# TODO: Once we have successfully upgraded to ES7, switch this back to ELASTIC_SEARCH_CONFIG.
ELASTIC_SEARCH_CONFIG = ENV_TOKENS.get('ELASTIC_SEARCH_CONFIG_ES7', [{}])

XBLOCK_SETTINGS = ENV_TOKENS.get('XBLOCK_SETTINGS', {})
XBLOCK_SETTINGS.setdefault("VideoBlock", {})["licensing_enabled"] = FEATURES.get("LICENSING", False)
XBLOCK_SETTINGS.setdefault("VideoBlock", {})['YOUTUBE_API_KEY'] = AUTH_TOKENS.get('YOUTUBE_API_KEY', YOUTUBE_API_KEY)

############################ OAUTH2 Provider ###################################

#### JWT configuration ####
JWT_AUTH.update(ENV_TOKENS.get('JWT_AUTH', {}))
JWT_AUTH.update(AUTH_TOKENS.get('JWT_AUTH', {}))

######################## CUSTOM COURSES for EDX CONNECTOR ######################
if FEATURES.get('CUSTOM_COURSES_EDX'):
    INSTALLED_APPS.append('openedx.core.djangoapps.ccxcon.apps.CCXConnectorConfig')

########## Settings for video transcript migration tasks ############
VIDEO_TRANSCRIPT_MIGRATIONS_JOB_QUEUE = ENV_TOKENS.get('VIDEO_TRANSCRIPT_MIGRATIONS_JOB_QUEUE', DEFAULT_PRIORITY_QUEUE)

########## Settings youtube thumbnails scraper tasks ############
SCRAPE_YOUTUBE_THUMBNAILS_JOB_QUEUE = ENV_TOKENS.get('SCRAPE_YOUTUBE_THUMBNAILS_JOB_QUEUE', DEFAULT_PRIORITY_QUEUE)

########## Settings update search index task ############
UPDATE_SEARCH_INDEX_JOB_QUEUE = ENV_TOKENS.get('UPDATE_SEARCH_INDEX_JOB_QUEUE', DEFAULT_PRIORITY_QUEUE)

########################## Extra middleware classes  #######################

# Allow extra middleware classes to be added to the app through configuration.
MIDDLEWARE.extend(ENV_TOKENS.get('EXTRA_MIDDLEWARE_CLASSES', []))

########################## Settings for Completion API #####################

# Once a user has watched this percentage of a video, mark it as complete:
# (0.0 = 0%, 1.0 = 100%)
COMPLETION_VIDEO_COMPLETE_PERCENTAGE = ENV_TOKENS.get(
    'COMPLETION_VIDEO_COMPLETE_PERCENTAGE',
    COMPLETION_VIDEO_COMPLETE_PERCENTAGE,
)

####################### Enterprise Settings ######################

# A default dictionary to be used for filtering out enterprise customer catalog.
ENTERPRISE_CUSTOMER_CATALOG_DEFAULT_CONTENT_FILTER = ENV_TOKENS.get(
    'ENTERPRISE_CUSTOMER_CATALOG_DEFAULT_CONTENT_FILTER',
    ENTERPRISE_CUSTOMER_CATALOG_DEFAULT_CONTENT_FILTER
)
ENTERPRISE_CATALOG_INTERNAL_ROOT_URL = ENV_TOKENS.get(
    'ENTERPRISE_CATALOG_INTERNAL_ROOT_URL',
    ENTERPRISE_CATALOG_INTERNAL_ROOT_URL
)
INTEGRATED_CHANNELS_API_CHUNK_TRANSMISSION_LIMIT = ENV_TOKENS.get(
    'INTEGRATED_CHANNELS_API_CHUNK_TRANSMISSION_LIMIT',
    INTEGRATED_CHANNELS_API_CHUNK_TRANSMISSION_LIMIT
)

############### Settings for Retirement #####################
RETIREMENT_SERVICE_WORKER_USERNAME = ENV_TOKENS.get(
    'RETIREMENT_SERVICE_WORKER_USERNAME',
    RETIREMENT_SERVICE_WORKER_USERNAME
)

############### Settings for Exams ####################
EXAMS_SERVICE_URL = ENV_TOKENS.get('EXAMS_SERVICE_URL', EXAMS_SERVICE_URL)
EXAMS_SERVICE_USERNAME = ENV_TOKENS.get('EXAMS_SERVICE_USERNAME', EXAMS_SERVICE_USERNAME)

############### Settings for edx-rbac  ###############
SYSTEM_WIDE_ROLE_CLASSES = ENV_TOKENS.get('SYSTEM_WIDE_ROLE_CLASSES') or SYSTEM_WIDE_ROLE_CLASSES

######################## Setting for content libraries ########################
MAX_BLOCKS_PER_CONTENT_LIBRARY = ENV_TOKENS.get('MAX_BLOCKS_PER_CONTENT_LIBRARY', MAX_BLOCKS_PER_CONTENT_LIBRARY)

########################## Derive Any Derived Settings  #######################

derive_settings(__name__)

####################### Plugin Settings ##########################

# This is at the bottom because it is going to load more settings after base settings are loaded

add_plugins(__name__, ProjectType.CMS, SettingsType.PRODUCTION)

############# CORS headers for cross-domain requests #################
if FEATURES.get('ENABLE_CORS_HEADERS'):
    CORS_ALLOW_CREDENTIALS = True
    CORS_ORIGIN_WHITELIST = ENV_TOKENS.get('CORS_ORIGIN_WHITELIST', ())

    CORS_ORIGIN_ALLOW_ALL = ENV_TOKENS.get('CORS_ORIGIN_ALLOW_ALL', False)
    CORS_ALLOW_INSECURE = ENV_TOKENS.get('CORS_ALLOW_INSECURE', False)

################# Settings for brand logos. #################
LOGO_URL = ENV_TOKENS.get('LOGO_URL', LOGO_URL)
LOGO_URL_PNG = ENV_TOKENS.get('LOGO_URL_PNG', LOGO_URL_PNG)
LOGO_TRADEMARK_URL = ENV_TOKENS.get('LOGO_TRADEMARK_URL', LOGO_TRADEMARK_URL)
FAVICON_URL = ENV_TOKENS.get('FAVICON_URL', FAVICON_URL)

######################## CELERY ROTUING ########################

# Defines alternate environment tasks, as a dict of form { task_name: alternate_queue }
ALTERNATE_ENV_TASKS = {
    'completion_aggregator.tasks.update_aggregators': 'lms',
    'openedx.core.djangoapps.content.block_structure.tasks.update_course_in_cache': 'lms',
    'openedx.core.djangoapps.content.block_structure.tasks.update_course_in_cache_v2': 'lms',
}

# Defines the task -> alternate worker queue to be used when routing.
EXPLICIT_QUEUES = {
    'lms.djangoapps.grades.tasks.compute_all_grades_for_course': {
        'queue': POLICY_CHANGE_GRADES_ROUTING_KEY},
    'lms.djangoapps.grades.tasks.recalculate_course_and_subsection_grades_for_user': {
        'queue': SINGLE_LEARNER_COURSE_REGRADE_ROUTING_KEY},
    'cms.djangoapps.contentstore.tasks.update_search_index': {
        'queue': UPDATE_SEARCH_INDEX_JOB_QUEUE},
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

LANGUAGE_COOKIE_NAME = ENV_TOKENS.get('LANGUAGE_COOKIE', None) or ENV_TOKENS.get(
    'LANGUAGE_COOKIE_NAME', LANGUAGE_COOKIE_NAME)

################# Discussions micro frontend URL ########################
DISCUSSIONS_MICROFRONTEND_URL = ENV_TOKENS.get('DISCUSSIONS_MICROFRONTEND_URL', DISCUSSIONS_MICROFRONTEND_URL)

################### Discussions micro frontend Feedback URL###################
DISCUSSIONS_MFE_FEEDBACK_URL = ENV_TOKENS.get('DISCUSSIONS_MFE_FEEDBACK_URL', DISCUSSIONS_MFE_FEEDBACK_URL)

############################ AI_TRANSLATIONS URL ##################################
AI_TRANSLATIONS_API_URL = ENV_TOKENS.get('AI_TRANSLATIONS_API_URL', AI_TRANSLATIONS_API_URL)

############## DRF overrides ##############
REST_FRAMEWORK.update(ENV_TOKENS.get('REST_FRAMEWORK', {}))

# keys for  big blue button live provider
COURSE_LIVE_GLOBAL_CREDENTIALS["BIG_BLUE_BUTTON"] = {
    "KEY": ENV_TOKENS.get('BIG_BLUE_BUTTON_GLOBAL_KEY', None),
    "SECRET": ENV_TOKENS.get('BIG_BLUE_BUTTON_GLOBAL_SECRET', None),
    "URL": ENV_TOKENS.get('BIG_BLUE_BUTTON_GLOBAL_URL', None),
}

INACTIVE_USER_URL = f'http{"s" if HTTPS == "on" else ""}://{CMS_BASE}'

############## Event bus producer ##############
EVENT_BUS_PRODUCER_CONFIG = merge_producer_configs(EVENT_BUS_PRODUCER_CONFIG,
                                                   ENV_TOKENS.get('EVENT_BUS_PRODUCER_CONFIG', {}))

############## Authoring API drf-spectacular openapi settings ##############
# These fields override the spectacular settings default values.
# Any fields not included here will use the default values.
SPECTACULAR_SETTINGS = {
    'TITLE': 'Authoring API',
    'DESCRIPTION': f'''Experimental API to edit xblocks and course content.
    \n\nDanger: Do not use on running courses!
    \n\n - How to gain access: Please email the owners of this openedx service.
    \n - How to use: This API uses oauth2 authentication with the
    access token endpoint: `{LMS_ROOT_URL}/oauth2/access_token`.
    Please see separately provided documentation.
    \n - How to test: You must be logged in as course author for whatever course you want to test with.
    You can use the [Swagger UI](https://{CMS_BASE}/authoring-api/ui/) to "Try out" the API with your test course. To do this, you must select the "Local" server.
    \n - Public vs. Local servers: The "Public" server is where you can reach the API externally. The "Local" server is
    for development with a local edx-platform version,  and for use via the [Swagger UI](https://{CMS_BASE}/authoring-api/ui/).
    \n - Swaggerfile: [Download link](https://{CMS_BASE}/authoring-api/schema/)''',
    'VERSION': '0.1.0',
    'SERVE_INCLUDE_SCHEMA': False,
    # restrict spectacular to CMS API endpoints (cms/lib/spectacular.py):
    'PREPROCESSING_HOOKS': ['cms.lib.spectacular.cms_api_filter'],
    # remove the default schema path prefix to replace it with server-specific base paths:
    'SCHEMA_PATH_PREFIX': '/api/contentstore',
    'SCHEMA_PATH_PREFIX_TRIM': '/api/contentstore',
    'SERVERS': [
        {'url': AUTHORING_API_URL, 'description': 'Public'},
        {'url': f'https://{CMS_BASE}/api/contentstore', 'description': 'Local'},
    ],
}

BEAMER_PRODUCT_ID = ENV_TOKENS.get('BEAMER_PRODUCT_ID', BEAMER_PRODUCT_ID)

# .. setting_name: DISABLED_COUNTRIES
# .. setting_default: []
# .. setting_description: List of country codes that should be disabled
# .. for now it wil impact country listing in auth flow and user profile.
# .. eg ['US', 'CA']
DISABLED_COUNTRIES = ENV_TOKENS.get('DISABLED_COUNTRIES', [])
