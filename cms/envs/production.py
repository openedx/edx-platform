"""
This is the default template for our main set of AWS servers.
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=wildcard-import, unused-wildcard-import


import codecs
import copy
import os
import yaml

from corsheaders.defaults import default_headers as corsheaders_default_headers
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse_lazy
from edx_django_utils.plugins import add_plugins
from path import Path as path

from openedx.core.djangoapps.plugins.constants import ProjectType, SettingsType

from .common import *

from openedx.core.lib.derived import derive_settings
from openedx.core.lib.logsettings import get_logger_config
from xmodule.modulestore.modulestore_settings import convert_module_store_setting_if_needed


def get_env_setting(setting):
    """ Get the environment setting or return exception """
    try:
        return os.environ[setting]
    except KeyError:
        error_msg = u"Set the %s env variable" % setting
        raise ImproperlyConfigured(error_msg)

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
CONFIG_FILE = get_env_setting('STUDIO_CFG')

with codecs.open(CONFIG_FILE, encoding='utf-8') as f:
    EDXAPP_CONFIG = yaml.safe_load(f)

    # ENV_TOKENS and AUTH_TOKENS are included for reverse compatability.
    # Removing them may break external plugins that rely on them.
    ENV_TOKENS = EDXAPP_CONFIG
    AUTH_TOKENS = EDXAPP_CONFIG

    # Add the key/values from config into the global namespace of this module.
    # For certain special dicts, merge their contents instead.

    __EDXAPP_CONFIG_COPY__ = copy.deepcopy(EDXAPP_CONFIG)

    KEYS_WITH_MERGED_VALUES = [
        'FEATURES',
        'TRACKING_BACKENDS',
        'EVENT_TRACKING_BACKENDS',
        'JWT_AUTH',
        'CELERY_QUEUES',
        'MKTG_URL_LINK_MAP',
        'MKTG_URL_OVERRIDES',
    ]
    for key in KEYS_WITH_MERGED_VALUES:
        if key in __EDXAPP_CONFIG_COPY__:
            del __EDXAPP_CONFIG_COPY__[key]

    vars().update(__EDXAPP_CONFIG_COPY__)


try:
    # A file path to a YAML file from which to load all the code revisions currently deployed
    REVISION_CONFIG_FILE = get_env_setting('REVISION_CFG')

    with codecs.open(REVISION_CONFIG_FILE, encoding='utf-8') as f:
        REVISION_CONFIG = yaml.safe_load(f)
except Exception:  # pylint: disable=broad-except
    REVISION_CONFIG = {}

# Do NOT calculate this dynamically at startup with git because it's *slow*.
EDX_PLATFORM_REVISION = REVISION_CONFIG.get('EDX_PLATFORM_REVISION', EDX_PLATFORM_REVISION)

# SERVICE_VARIANT specifies name of the variant used, which decides what JSON
# configuration files are read during startup.
SERVICE_VARIANT = os.environ.get('SERVICE_VARIANT', None)

# CONFIG_PREFIX specifies the prefix of the JSON configuration files,
# based on the service variant. If no variant is use, don't use a
# prefix.
CONFIG_PREFIX = SERVICE_VARIANT + "." if SERVICE_VARIANT else ""

###################################### CELERY  ################################

# Don't use a connection pool, since connections are dropped by ELB.
BROKER_POOL_LIMIT = 0
BROKER_CONNECTION_TIMEOUT = 1

# For the Result Store, use the django cache named 'celery'
CELERY_RESULT_BACKEND = 'django-cache'

# When the broker is behind an ELB, use a heartbeat to refresh the
# connection and to detect if it has been dropped.
BROKER_HEARTBEAT = EDXAPP_CONFIG.get('BROKER_HEARTBEAT', 60.0)
BROKER_HEARTBEAT_CHECKRATE = EDXAPP_CONFIG.get('BROKER_HEARTBEAT_CHECKRATE', 2)

# Each worker should only fetch one message at a time
CELERYD_PREFETCH_MULTIPLIER = 1

# Rename the exchange and queues for each variant

QUEUE_VARIANT = CONFIG_PREFIX.lower()

CELERY_DEFAULT_EXCHANGE = 'edx.{0}core'.format(QUEUE_VARIANT)

HIGH_PRIORITY_QUEUE = 'edx.{0}core.high'.format(QUEUE_VARIANT)
DEFAULT_PRIORITY_QUEUE = 'edx.{0}core.default'.format(QUEUE_VARIANT)

CELERY_DEFAULT_QUEUE = DEFAULT_PRIORITY_QUEUE
CELERY_DEFAULT_ROUTING_KEY = DEFAULT_PRIORITY_QUEUE

CELERY_QUEUES = {
    HIGH_PRIORITY_QUEUE: {},
    DEFAULT_PRIORITY_QUEUE: {}
}

CELERY_ROUTES = "{}celery.Router".format(QUEUE_VARIANT)

# STATIC_URL_BASE specifies the base url to use for static files
STATIC_URL_BASE = EDXAPP_CONFIG.get('STATIC_URL_BASE', None)
if STATIC_URL_BASE:
    STATIC_URL = STATIC_URL_BASE
    if not STATIC_URL.endswith("/"):
        STATIC_URL += "/"
    STATIC_URL += 'studio/'

DEFAULT_COURSE_VISIBILITY_IN_CATALOG = EDXAPP_CONFIG.get(
    'DEFAULT_COURSE_VISIBILITY_IN_CATALOG',
    DEFAULT_COURSE_VISIBILITY_IN_CATALOG
)

# DEFAULT_MOBILE_AVAILABLE specifies if the course is available for mobile by default
DEFAULT_MOBILE_AVAILABLE = EDXAPP_CONFIG.get(
    'DEFAULT_MOBILE_AVAILABLE',
    DEFAULT_MOBILE_AVAILABLE
)

# How long to cache OpenAPI schemas and UI, in seconds.
OPENAPI_CACHE_TIMEOUT = EDXAPP_CONFIG.get('OPENAPI_CACHE_TIMEOUT', 60 * 60)

# STATIC_ROOT specifies the directory where static files are
# collected

STATIC_ROOT_BASE = EDXAPP_CONFIG.get('STATIC_ROOT_BASE', None)
if STATIC_ROOT_BASE:
    STATIC_ROOT = path(STATIC_ROOT_BASE) / 'studio'
    WEBPACK_LOADER['DEFAULT']['STATS_FILE'] = STATIC_ROOT / "webpack-stats.json"
    WEBPACK_LOADER['WORKERS']['STATS_FILE'] = STATIC_ROOT / "webpack-worker-stats.json"

EMAIL_FILE_PATH = EDXAPP_CONFIG.get('EMAIL_FILE_PATH', None)


# CMS_BASE: Public domain name of Studio (should be resolvable from the end-user's browser)
CMS_BASE = EDXAPP_CONFIG.get('CMS_BASE')
LMS_BASE = EDXAPP_CONFIG.get('LMS_BASE')
LMS_ROOT_URL = EDXAPP_CONFIG.get('LMS_ROOT_URL')
LMS_INTERNAL_ROOT_URL = EDXAPP_CONFIG.get('LMS_INTERNAL_ROOT_URL', LMS_ROOT_URL)
ENTERPRISE_API_URL = EDXAPP_CONFIG.get('ENTERPRISE_API_URL', LMS_INTERNAL_ROOT_URL + '/enterprise/api/v1/')
ENTERPRISE_CONSENT_API_URL = EDXAPP_CONFIG.get('ENTERPRISE_CONSENT_API_URL', LMS_INTERNAL_ROOT_URL + '/consent/api/v1/')
# Note that FEATURES['PREVIEW_LMS_BASE'] gets read in from the environment file.


# List of logout URIs for each IDA that the learner should be logged out of when they logout of
# Studio. Only applies to IDA for which the social auth flow uses DOT (Django OAuth Toolkit).
IDA_LOGOUT_URI_LIST = EDXAPP_CONFIG.get('IDA_LOGOUT_URI_LIST', [])

SITE_NAME = EDXAPP_CONFIG['SITE_NAME']

ALLOWED_HOSTS = [
    # TODO: bbeggs remove this before prod, temp fix to get load testing running
    "*",
    CMS_BASE,
]

LOG_DIR = EDXAPP_CONFIG['LOG_DIR']
DATA_DIR = path(EDXAPP_CONFIG.get('DATA_DIR', DATA_DIR))

CACHES = EDXAPP_CONFIG['CACHES']
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
STATICFILES_STORAGE = os.environ.get(
    'STATICFILES_STORAGE',
    EDXAPP_CONFIG.get('STATICFILES_STORAGE', STATICFILES_STORAGE),
)

# Load all AWS_ prefixed variables to allow an S3Boto3Storage to be configured
_locals = locals()
for key, value in EDXAPP_CONFIG.items():
    if key.startswith('AWS_'):
        _locals[key] = value

SESSION_COOKIE_DOMAIN = EDXAPP_CONFIG.get('SESSION_COOKIE_DOMAIN')
SESSION_COOKIE_HTTPONLY = EDXAPP_CONFIG.get('SESSION_COOKIE_HTTPONLY', True)

REGISTRATION_EMAIL_PATTERNS_ALLOWED = EDXAPP_CONFIG.get('REGISTRATION_EMAIL_PATTERNS_ALLOWED')

# allow for environments to specify what cookie name our login subsystem should use
# this is to fix a bug regarding simultaneous logins between edx.org and edge.edx.org which can
# happen with some browsers (e.g. Firefox)
if EDXAPP_CONFIG.get('SESSION_COOKIE_NAME', None):
    # NOTE, there's a bug in Django (http://bugs.python.org/issue18012) which necessitates this being a str()
    SESSION_COOKIE_NAME = str(EDXAPP_CONFIG.get('SESSION_COOKIE_NAME'))

# Determines whether the CSRF token can be transported on
# unencrypted channels. It is set to False here for backward compatibility,
# but it is highly recommended that this is True for environments accessed
# by end users.
CSRF_COOKIE_SECURE = EDXAPP_CONFIG.get('CSRF_COOKIE_SECURE', False)

#Email overrides
MKTG_URL_LINK_MAP.update(EDXAPP_CONFIG.get('MKTG_URL_LINK_MAP', {}))
MKTG_URL_OVERRIDES.update(EDXAPP_CONFIG.get('MKTG_URL_OVERRIDES', MKTG_URL_OVERRIDES))

for name, value in EDXAPP_CONFIG.get("CODE_JAIL", {}).items():
    oldvalue = CODE_JAIL.get(name)
    if isinstance(oldvalue, dict):
        for subname, subvalue in value.items():
            oldvalue[subname] = subvalue
    else:
        CODE_JAIL[name] = value

COURSES_WITH_UNSAFE_CODE = EDXAPP_CONFIG.get("COURSES_WITH_UNSAFE_CODE", [])

# COMPREHENSIVE_THEME_LOCALE_PATHS contain the paths to themes locale directories e.g.
# "COMPREHENSIVE_THEME_LOCALE_PATHS" : [
#        "/edx/src/edx-themes/conf/locale"
#    ],
COMPREHENSIVE_THEME_LOCALE_PATHS = EDXAPP_CONFIG.get('COMPREHENSIVE_THEME_LOCALE_PATHS', [])

#Timezone overrides
TIME_ZONE = EDXAPP_CONFIG.get('CELERY_TIMEZONE', CELERY_TIMEZONE)

##### REGISTRATION RATE LIMIT SETTINGS #####
REGISTRATION_VALIDATION_RATELIMIT = EDXAPP_CONFIG.get(
    'REGISTRATION_VALIDATION_RATELIMIT', REGISTRATION_VALIDATION_RATELIMIT
)

# Push to LMS overrides
GIT_REPO_EXPORT_DIR = EDXAPP_CONFIG.get('GIT_REPO_EXPORT_DIR', '/edx/var/edxapp/export_course_repos')

ENV_FEATURES = EDXAPP_CONFIG.get('FEATURES', {})
for feature, value in ENV_FEATURES.items():
    FEATURES[feature] = value

# Additional installed apps
for app in EDXAPP_CONFIG.get('ADDL_INSTALLED_APPS', []):
    INSTALLED_APPS.append(app)

LOGGING = get_logger_config(LOG_DIR,
                            logging_env=EDXAPP_CONFIG['LOGGING_ENV'],
                            service_variant=SERVICE_VARIANT)

# The following variables use (or) instead of the default value inside (get). This is to enforce using the Lazy Text
# values when the varibale is an empty string. Therefore, setting these variable as empty text in related
# json files will make the system reads thier values from django translation files
PLATFORM_NAME = EDXAPP_CONFIG.get('PLATFORM_NAME') or PLATFORM_NAME
PLATFORM_DESCRIPTION = EDXAPP_CONFIG.get('PLATFORM_DESCRIPTION') or PLATFORM_DESCRIPTION
STUDIO_NAME = EDXAPP_CONFIG.get('STUDIO_NAME') or STUDIO_NAME
STUDIO_SHORT_NAME = EDXAPP_CONFIG.get('STUDIO_SHORT_NAME') or STUDIO_SHORT_NAME

# Event Tracking
if "TRACKING_IGNORE_URL_PATTERNS" in EDXAPP_CONFIG:
    TRACKING_IGNORE_URL_PATTERNS = EDXAPP_CONFIG.get("TRACKING_IGNORE_URL_PATTERNS")

# Heartbeat
HEARTBEAT_CELERY_ROUTING_KEY = EDXAPP_CONFIG.get('HEARTBEAT_CELERY_ROUTING_KEY', HEARTBEAT_CELERY_ROUTING_KEY)

LOGIN_REDIRECT_WHITELIST = [reverse_lazy('home')]


############### XBlock filesystem field config ##########
if 'DJFS' in EDXAPP_CONFIG and EDXAPP_CONFIG['DJFS'] is not None:
    DJFS = EDXAPP_CONFIG['DJFS']
    if 'url_root' in DJFS:
        DJFS['url_root'] = DJFS['url_root'].format(platform_revision=EDX_PLATFORM_REVISION)


AWS_SES_REGION_NAME = EDXAPP_CONFIG.get('AWS_SES_REGION_NAME', 'us-east-1')
AWS_SES_REGION_ENDPOINT = EDXAPP_CONFIG.get('AWS_SES_REGION_ENDPOINT', 'email.us-east-1.amazonaws.com')

# Note that this is the Studio key for Segment. There is a separate key for the LMS.
CMS_SEGMENT_KEY = EDXAPP_CONFIG.get('SEGMENT_KEY')

SECRET_KEY = EDXAPP_CONFIG['SECRET_KEY']

AWS_ACCESS_KEY_ID = EDXAPP_CONFIG["AWS_ACCESS_KEY_ID"]
if AWS_ACCESS_KEY_ID == "":
    AWS_ACCESS_KEY_ID = None

AWS_SECRET_ACCESS_KEY = EDXAPP_CONFIG["AWS_SECRET_ACCESS_KEY"]
if AWS_SECRET_ACCESS_KEY == "":
    AWS_SECRET_ACCESS_KEY = None

AWS_STORAGE_BUCKET_NAME = EDXAPP_CONFIG.get('AWS_STORAGE_BUCKET_NAME', 'edxuploads')

# Disabling querystring auth instructs Boto to exclude the querystring parameters (e.g. signature, access key) it
# normally appends to every returned URL.
AWS_QUERYSTRING_AUTH = EDXAPP_CONFIG.get('AWS_QUERYSTRING_AUTH', True)

AWS_DEFAULT_ACL = 'private'
AWS_BUCKET_ACL = AWS_DEFAULT_ACL
AWS_QUERYSTRING_EXPIRE = 7 * 24 * 60 * 60  # 7 days
AWS_S3_CUSTOM_DOMAIN = EDXAPP_CONFIG.get('AWS_S3_CUSTOM_DOMAIN', 'edxuploads.s3.amazonaws.com')

if EDXAPP_CONFIG.get('DEFAULT_FILE_STORAGE'):
    DEFAULT_FILE_STORAGE = EDXAPP_CONFIG.get('DEFAULT_FILE_STORAGE')
elif AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
else:
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

COURSE_IMPORT_EXPORT_BUCKET = EDXAPP_CONFIG.get('COURSE_IMPORT_EXPORT_BUCKET', '')

if COURSE_IMPORT_EXPORT_BUCKET:
    COURSE_IMPORT_EXPORT_STORAGE = 'cms.djangoapps.contentstore.storage.ImportExportS3Storage'
else:
    COURSE_IMPORT_EXPORT_STORAGE = DEFAULT_FILE_STORAGE

USER_TASKS_ARTIFACT_STORAGE = COURSE_IMPORT_EXPORT_STORAGE

DATABASES = EDXAPP_CONFIG['DATABASES']

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

MODULESTORE = convert_module_store_setting_if_needed(EDXAPP_CONFIG.get('MODULESTORE', MODULESTORE))

MODULESTORE_FIELD_OVERRIDE_PROVIDERS = EDXAPP_CONFIG.get(
    'MODULESTORE_FIELD_OVERRIDE_PROVIDERS',
    MODULESTORE_FIELD_OVERRIDE_PROVIDERS
)

XBLOCK_FIELD_DATA_WRAPPERS = EDXAPP_CONFIG.get(
    'XBLOCK_FIELD_DATA_WRAPPERS',
    XBLOCK_FIELD_DATA_WRAPPERS
)

CONTENTSTORE = EDXAPP_CONFIG['CONTENTSTORE']
DOC_STORE_CONFIG = EDXAPP_CONFIG['DOC_STORE_CONFIG']

############################### BLOCKSTORE #####################################
BLOCKSTORE_API_URL = EDXAPP_CONFIG.get('BLOCKSTORE_API_URL', None)  # e.g. "https://blockstore.example.com/api/v1/"
# Configure an API auth token at (blockstore URL)/admin/authtoken/token/
BLOCKSTORE_API_AUTH_TOKEN = EDXAPP_CONFIG.get('BLOCKSTORE_API_AUTH_TOKEN', None)

# Datadog for events!
DATADOG = EDXAPP_CONFIG.get("DATADOG", {})
DATADOG.update(EDXAPP_CONFIG.get("DATADOG", {}))

# TODO: deprecated (compatibility with previous settings)
if 'DATADOG_API' in EDXAPP_CONFIG:
    DATADOG['api_key'] = EDXAPP_CONFIG['DATADOG_API']

# Celery Broker
CELERY_ALWAYS_EAGER = EDXAPP_CONFIG.get("CELERY_ALWAYS_EAGER", False)
CELERY_BROKER_TRANSPORT = EDXAPP_CONFIG.get("CELERY_BROKER_TRANSPORT", "")
CELERY_BROKER_HOSTNAME = EDXAPP_CONFIG.get("CELERY_BROKER_HOSTNAME", "")
CELERY_BROKER_VHOST = EDXAPP_CONFIG.get("CELERY_BROKER_VHOST", "")
CELERY_BROKER_USER = EDXAPP_CONFIG.get("CELERY_BROKER_USER", "")
CELERY_BROKER_PASSWORD = EDXAPP_CONFIG.get("CELERY_BROKER_PASSWORD", "")

BROKER_URL = "{0}://{1}:{2}@{3}/{4}".format(CELERY_BROKER_TRANSPORT,
                                            CELERY_BROKER_USER,
                                            CELERY_BROKER_PASSWORD,
                                            CELERY_BROKER_HOSTNAME,
                                            CELERY_BROKER_VHOST)
BROKER_USE_SSL = EDXAPP_CONFIG.get('CELERY_BROKER_USE_SSL', False)

BROKER_TRANSPORT_OPTIONS = {
    'fanout_patterns': True,
    'fanout_prefix': True,
}

# Message expiry time in seconds
CELERY_EVENT_QUEUE_TTL = EDXAPP_CONFIG.get('CELERY_EVENT_QUEUE_TTL', None)

# Allow CELERY_QUEUES to be overwritten by EDXAPP_CONFIG,
ENV_CELERY_QUEUES = EDXAPP_CONFIG.get('CELERY_QUEUES', None)
if ENV_CELERY_QUEUES:
    CELERY_QUEUES = {queue: {} for queue in ENV_CELERY_QUEUES}

# Then add alternate environment queues
ALTERNATE_QUEUE_ENVS = EDXAPP_CONFIG.get('ALTERNATE_WORKER_QUEUES', '').split()
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
POLICY_CHANGE_GRADES_ROUTING_KEY = EDXAPP_CONFIG.get('POLICY_CHANGE_GRADES_ROUTING_KEY', DEFAULT_PRIORITY_QUEUE)

SOFTWARE_SECURE_VERIFICATION_ROUTING_KEY = EDXAPP_CONFIG.get(
    'SOFTWARE_SECURE_VERIFICATION_ROUTING_KEY',
    HIGH_PRIORITY_QUEUE
)

# Event tracking
TRACKING_BACKENDS.update(EDXAPP_CONFIG.get("TRACKING_BACKENDS", {}))
EVENT_TRACKING_BACKENDS['tracking_logs']['OPTIONS']['backends'].update(
    EDXAPP_CONFIG.get("EVENT_TRACKING_BACKENDS", {})
)
EVENT_TRACKING_BACKENDS['segmentio']['OPTIONS']['processors'][0]['OPTIONS']['whitelist'].extend(
    EDXAPP_CONFIG.get("EVENT_TRACKING_SEGMENTIO_EMIT_WHITELIST", []))

##### ACCOUNT LOCKOUT DEFAULT PARAMETERS #####
MAX_FAILED_LOGIN_ATTEMPTS_ALLOWED = EDXAPP_CONFIG.get(
    "MAX_FAILED_LOGIN_ATTEMPTS_ALLOWED", MAX_FAILED_LOGIN_ATTEMPTS_ALLOWED
)

MAX_FAILED_LOGIN_ATTEMPTS_LOCKOUT_PERIOD_SECS = EDXAPP_CONFIG.get(
    "MAX_FAILED_LOGIN_ATTEMPTS_LOCKOUT_PERIOD_SECS", MAX_FAILED_LOGIN_ATTEMPTS_LOCKOUT_PERIOD_SECS
)

#### PASSWORD POLICY SETTINGS #####
AUTH_PASSWORD_VALIDATORS = EDXAPP_CONFIG.get("AUTH_PASSWORD_VALIDATORS", AUTH_PASSWORD_VALIDATORS)

### INACTIVITY SETTINGS ####
SESSION_INACTIVITY_TIMEOUT_IN_SECONDS = EDXAPP_CONFIG.get("SESSION_INACTIVITY_TIMEOUT_IN_SECONDS")

################ PUSH NOTIFICATIONS ###############
PARSE_KEYS = EDXAPP_CONFIG.get("PARSE_KEYS", {})


# Video Caching. Pairing country codes with CDN URLs.
# Example: {'CN': 'http://api.xuetangx.com/edx/video?s3_url='}
VIDEO_CDN_URL = EDXAPP_CONFIG.get('VIDEO_CDN_URL', {})

if FEATURES['ENABLE_COURSEWARE_INDEX'] or FEATURES['ENABLE_LIBRARY_INDEX'] or FEATURES['ENABLE_CONTENT_LIBRARY_INDEX']:
    # Use ElasticSearch for the search engine
    SEARCH_ENGINE = "search.elastic.ElasticSearchEngine"

# TODO: Once we have successfully upgraded to ES7, switch this back to ELASTIC_SEARCH_CONFIG.
ELASTIC_SEARCH_CONFIG = EDXAPP_CONFIG.get('ELASTIC_SEARCH_CONFIG_ES7', [{}])

XBLOCK_SETTINGS = EDXAPP_CONFIG.get('XBLOCK_SETTINGS', {})
XBLOCK_SETTINGS.setdefault("VideoBlock", {})["licensing_enabled"] = FEATURES.get("LICENSING", False)
XBLOCK_SETTINGS.setdefault("VideoBlock", {})['YOUTUBE_API_KEY'] = EDXAPP_CONFIG.get('YOUTUBE_API_KEY', YOUTUBE_API_KEY)

############################ OAUTH2 Provider ###################################

#### JWT configuration ####
JWT_AUTH.update(EDXAPP_CONFIG.get('JWT_AUTH', {}))
JWT_AUTH.update(EDXAPP_CONFIG.get('JWT_AUTH', {}))

######################## CUSTOM COURSES for EDX CONNECTOR ######################
if FEATURES.get('CUSTOM_COURSES_EDX'):
    INSTALLED_APPS.append('openedx.core.djangoapps.ccxcon.apps.CCXConnectorConfig')

############## Settings for CourseGraph ############################
COURSEGRAPH_JOB_QUEUE = EDXAPP_CONFIG.get('COURSEGRAPH_JOB_QUEUE', DEFAULT_PRIORITY_QUEUE)

########## Settings for video transcript migration tasks ############
VIDEO_TRANSCRIPT_MIGRATIONS_JOB_QUEUE = EDXAPP_CONFIG.get(
    'VIDEO_TRANSCRIPT_MIGRATIONS_JOB_QUEUE',
    DEFAULT_PRIORITY_QUEUE,
)

########## Settings youtube thumbnails scraper tasks ############
SCRAPE_YOUTUBE_THUMBNAILS_JOB_QUEUE = EDXAPP_CONFIG.get('SCRAPE_YOUTUBE_THUMBNAILS_JOB_QUEUE', DEFAULT_PRIORITY_QUEUE)

########## Settings update search index task ############
UPDATE_SEARCH_INDEX_JOB_QUEUE = EDXAPP_CONFIG.get('UPDATE_SEARCH_INDEX_JOB_QUEUE', DEFAULT_PRIORITY_QUEUE)

########################## Extra middleware classes  #######################

# Allow extra middleware classes to be added to the app through configuration.
MIDDLEWARE.extend(EDXAPP_CONFIG.get('EXTRA_MIDDLEWARE_CLASSES', []))

########################## Settings for Completion API #####################

# Once a user has watched this percentage of a video, mark it as complete:
# (0.0 = 0%, 1.0 = 100%)
COMPLETION_VIDEO_COMPLETE_PERCENTAGE = EDXAPP_CONFIG.get(
    'COMPLETION_VIDEO_COMPLETE_PERCENTAGE',
    COMPLETION_VIDEO_COMPLETE_PERCENTAGE,
)

####################### Enterprise Settings ######################

# A default dictionary to be used for filtering out enterprise customer catalog.
ENTERPRISE_CUSTOMER_CATALOG_DEFAULT_CONTENT_FILTER = EDXAPP_CONFIG.get(
    'ENTERPRISE_CUSTOMER_CATALOG_DEFAULT_CONTENT_FILTER',
    ENTERPRISE_CUSTOMER_CATALOG_DEFAULT_CONTENT_FILTER
)
ENTERPRISE_CATALOG_INTERNAL_ROOT_URL = EDXAPP_CONFIG.get(
    'ENTERPRISE_CATALOG_INTERNAL_ROOT_URL',
    ENTERPRISE_CATALOG_INTERNAL_ROOT_URL
)
INTEGRATED_CHANNELS_API_CHUNK_TRANSMISSION_LIMIT = EDXAPP_CONFIG.get(
    'INTEGRATED_CHANNELS_API_CHUNK_TRANSMISSION_LIMIT',
    INTEGRATED_CHANNELS_API_CHUNK_TRANSMISSION_LIMIT
)

############### Settings for Retirement #####################
RETIREMENT_SERVICE_WORKER_USERNAME = EDXAPP_CONFIG.get(
    'RETIREMENT_SERVICE_WORKER_USERNAME',
    RETIREMENT_SERVICE_WORKER_USERNAME
)

############### Settings for edx-rbac  ###############
SYSTEM_WIDE_ROLE_CLASSES = EDXAPP_CONFIG.get('SYSTEM_WIDE_ROLE_CLASSES') or SYSTEM_WIDE_ROLE_CLASSES

######################## Setting for content libraries ########################
MAX_BLOCKS_PER_CONTENT_LIBRARY = EDXAPP_CONFIG.get('MAX_BLOCKS_PER_CONTENT_LIBRARY', MAX_BLOCKS_PER_CONTENT_LIBRARY)

####################### Plugin Settings ##########################

# This is at the bottom because it is going to load more settings after base settings are loaded

add_plugins(__name__, ProjectType.CMS, SettingsType.PRODUCTION)

########################## Derive Any Derived Settings  #######################

derive_settings(__name__)

############# CORS headers for cross-domain requests #################
if FEATURES.get('ENABLE_CORS_HEADERS'):
    CORS_ALLOW_CREDENTIALS = True
    CORS_ORIGIN_WHITELIST = EDXAPP_CONFIG.get('CORS_ORIGIN_WHITELIST', ())
    CORS_ORIGIN_ALLOW_ALL = EDXAPP_CONFIG.get('CORS_ORIGIN_ALLOW_ALL', False)
    CORS_ALLOW_INSECURE = EDXAPP_CONFIG.get('CORS_ALLOW_INSECURE', False)
    CORS_ALLOW_HEADERS = corsheaders_default_headers + (
        'use-jwt-cookie',
    )

################# Settings for brand logos. #################
LOGO_URL = EDXAPP_CONFIG.get('LOGO_URL', LOGO_URL)
LOGO_URL_PNG = EDXAPP_CONFIG.get('LOGO_URL_PNG', LOGO_URL_PNG)
LOGO_TRADEMARK_URL = EDXAPP_CONFIG.get('LOGO_TRADEMARK_URL', LOGO_TRADEMARK_URL)
FAVICON_URL = EDXAPP_CONFIG.get('FAVICON_URL', FAVICON_URL)
