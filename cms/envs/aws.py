"""
This is the default template for our main set of AWS servers.
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=wildcard-import, unused-wildcard-import

# Pylint gets confused by path.py instances, which report themselves as class
# objects. As a result, pylint applies the wrong regex in validating names,
# and throws spurious errors. Therefore, we disable invalid-name checking.
# pylint: disable=invalid-name

import json

from .common import *

from openedx.core.lib.derived import derive_settings
from openedx.core.lib.logsettings import get_logger_config
import os

from path import Path as path
from xmodule.modulestore.modulestore_settings import convert_module_store_setting_if_needed

# SERVICE_VARIANT specifies name of the variant used, which decides what JSON
# configuration files are read during startup.
SERVICE_VARIANT = os.environ.get('SERVICE_VARIANT', None)

# CONFIG_ROOT specifies the directory where the JSON configuration
# files are expected to be found. If not specified, use the project
# directory.
CONFIG_ROOT = path(os.environ.get('CONFIG_ROOT', ENV_ROOT))

# CONFIG_PREFIX specifies the prefix of the JSON configuration files,
# based on the service variant. If no variant is use, don't use a
# prefix.
CONFIG_PREFIX = SERVICE_VARIANT + "." if SERVICE_VARIANT else ""


############### ALWAYS THE SAME ################################

DEBUG = False

EMAIL_BACKEND = 'django_ses.SESBackend'
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

# IMPORTANT: With this enabled, the server must always be behind a proxy that
# strips the header HTTP_X_FORWARDED_PROTO from client requests. Otherwise,
# a user can fool our server into thinking it was an https connection.
# See
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
# for other warnings.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

###################################### CELERY  ################################

# Don't use a connection pool, since connections are dropped by ELB.
BROKER_POOL_LIMIT = 0
BROKER_CONNECTION_TIMEOUT = 1

# For the Result Store, use the django cache named 'celery'
CELERY_RESULT_BACKEND = 'djcelery.backends.cache:CacheBackend'

# When the broker is behind an ELB, use a heartbeat to refresh the
# connection and to detect if it has been dropped.
BROKER_HEARTBEAT = 60.0
BROKER_HEARTBEAT_CHECKRATE = 2

# Each worker should only fetch one message at a time
CELERYD_PREFETCH_MULTIPLIER = 1

# Rename the exchange and queues for each variant

QUEUE_VARIANT = CONFIG_PREFIX.lower()

CELERY_DEFAULT_EXCHANGE = 'edx.{0}core'.format(QUEUE_VARIANT)

HIGH_PRIORITY_QUEUE = 'edx.{0}core.high'.format(QUEUE_VARIANT)
DEFAULT_PRIORITY_QUEUE = 'edx.{0}core.default'.format(QUEUE_VARIANT)
LOW_PRIORITY_QUEUE = 'edx.{0}core.low'.format(QUEUE_VARIANT)

CELERY_DEFAULT_QUEUE = DEFAULT_PRIORITY_QUEUE
CELERY_DEFAULT_ROUTING_KEY = DEFAULT_PRIORITY_QUEUE

CELERY_QUEUES = {
    HIGH_PRIORITY_QUEUE: {},
    LOW_PRIORITY_QUEUE: {},
    DEFAULT_PRIORITY_QUEUE: {}
}

CELERY_ROUTES = "{}celery.Router".format(QUEUE_VARIANT)

############# NON-SECURE ENV CONFIG ##############################
# Things like server locations, ports, etc.
with open(CONFIG_ROOT / CONFIG_PREFIX + "env.json") as env_file:
    ENV_TOKENS = json.load(env_file)

# STATIC_URL_BASE specifies the base url to use for static files
STATIC_URL_BASE = ENV_TOKENS.get('STATIC_URL_BASE', None)
if STATIC_URL_BASE:
    # collectstatic will fail if STATIC_URL is a unicode string
    STATIC_URL = STATIC_URL_BASE.encode('ascii')
    if not STATIC_URL.endswith("/"):
        STATIC_URL += "/"
    STATIC_URL += EDX_PLATFORM_REVISION + "/"

# DEFAULT_COURSE_ABOUT_IMAGE_URL specifies the default image to show for courses that don't provide one
DEFAULT_COURSE_ABOUT_IMAGE_URL = ENV_TOKENS.get('DEFAULT_COURSE_ABOUT_IMAGE_URL', DEFAULT_COURSE_ABOUT_IMAGE_URL)

# MEDIA_ROOT specifies the directory where user-uploaded files are stored.
MEDIA_ROOT = ENV_TOKENS.get('MEDIA_ROOT', MEDIA_ROOT)
MEDIA_URL = ENV_TOKENS.get('MEDIA_URL', MEDIA_URL)

# GITHUB_REPO_ROOT is the base directory
# for course data
GITHUB_REPO_ROOT = ENV_TOKENS.get('GITHUB_REPO_ROOT', GITHUB_REPO_ROOT)

# STATIC_ROOT specifies the directory where static files are
# collected

STATIC_ROOT_BASE = ENV_TOKENS.get('STATIC_ROOT_BASE', None)
if STATIC_ROOT_BASE:
    STATIC_ROOT = path(STATIC_ROOT_BASE) / EDX_PLATFORM_REVISION
    WEBPACK_LOADER['DEFAULT']['STATS_FILE'] = STATIC_ROOT / "webpack-stats.json"

EMAIL_BACKEND = ENV_TOKENS.get('EMAIL_BACKEND', EMAIL_BACKEND)
EMAIL_FILE_PATH = ENV_TOKENS.get('EMAIL_FILE_PATH', None)

EMAIL_HOST = ENV_TOKENS.get('EMAIL_HOST', EMAIL_HOST)
EMAIL_PORT = ENV_TOKENS.get('EMAIL_PORT', EMAIL_PORT)
EMAIL_USE_TLS = ENV_TOKENS.get('EMAIL_USE_TLS', EMAIL_USE_TLS)

LMS_BASE = ENV_TOKENS.get('LMS_BASE')
LMS_ROOT_URL = ENV_TOKENS.get('LMS_ROOT_URL')
# Note that FEATURES['PREVIEW_LMS_BASE'] gets read in from the environment file.

SITE_NAME = ENV_TOKENS['SITE_NAME']

ALLOWED_HOSTS = [
    # TODO: bbeggs remove this before prod, temp fix to get load testing running
    "*",
    ENV_TOKENS.get('CMS_BASE')
]

LOG_DIR = ENV_TOKENS['LOG_DIR']

CACHES = ENV_TOKENS['CACHES']
# Cache used for location mapping -- called many times with the same key/value
# in a given request.
if 'loc_cache' not in CACHES:
    CACHES['loc_cache'] = {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'edx_location_mem_cache',
    }

SESSION_COOKIE_DOMAIN = ENV_TOKENS.get('SESSION_COOKIE_DOMAIN')
SESSION_COOKIE_HTTPONLY = ENV_TOKENS.get('SESSION_COOKIE_HTTPONLY', True)
SESSION_ENGINE = ENV_TOKENS.get('SESSION_ENGINE', SESSION_ENGINE)
SESSION_COOKIE_SECURE = ENV_TOKENS.get('SESSION_COOKIE_SECURE', SESSION_COOKIE_SECURE)
SESSION_SAVE_EVERY_REQUEST = ENV_TOKENS.get('SESSION_SAVE_EVERY_REQUEST', SESSION_SAVE_EVERY_REQUEST)

# social sharing settings
SOCIAL_SHARING_SETTINGS = ENV_TOKENS.get('SOCIAL_SHARING_SETTINGS', SOCIAL_SHARING_SETTINGS)

REGISTRATION_EMAIL_PATTERNS_ALLOWED = ENV_TOKENS.get('REGISTRATION_EMAIL_PATTERNS_ALLOWED')

# allow for environments to specify what cookie name our login subsystem should use
# this is to fix a bug regarding simultaneous logins between edx.org and edge.edx.org which can
# happen with some browsers (e.g. Firefox)
if ENV_TOKENS.get('SESSION_COOKIE_NAME', None):
    # NOTE, there's a bug in Django (http://bugs.python.org/issue18012) which necessitates this being a str()
    SESSION_COOKIE_NAME = str(ENV_TOKENS.get('SESSION_COOKIE_NAME'))

# Set the names of cookies shared with the marketing site
# These have the same cookie domain as the session, which in production
# usually includes subdomains.
EDXMKTG_LOGGED_IN_COOKIE_NAME = ENV_TOKENS.get('EDXMKTG_LOGGED_IN_COOKIE_NAME', EDXMKTG_LOGGED_IN_COOKIE_NAME)
EDXMKTG_USER_INFO_COOKIE_NAME = ENV_TOKENS.get('EDXMKTG_USER_INFO_COOKIE_NAME', EDXMKTG_USER_INFO_COOKIE_NAME)

# Determines whether the CSRF token can be transported on
# unencrypted channels. It is set to False here for backward compatibility,
# but it is highly recommended that this is True for environments accessed
# by end users.
CSRF_COOKIE_SECURE = ENV_TOKENS.get('CSRF_COOKIE_SECURE', False)

#Email overrides
DEFAULT_FROM_EMAIL = ENV_TOKENS.get('DEFAULT_FROM_EMAIL', DEFAULT_FROM_EMAIL)
DEFAULT_FEEDBACK_EMAIL = ENV_TOKENS.get('DEFAULT_FEEDBACK_EMAIL', DEFAULT_FEEDBACK_EMAIL)
ADMINS = ENV_TOKENS.get('ADMINS', ADMINS)
SERVER_EMAIL = ENV_TOKENS.get('SERVER_EMAIL', SERVER_EMAIL)
MKTG_URLS = ENV_TOKENS.get('MKTG_URLS', MKTG_URLS)
TECH_SUPPORT_EMAIL = ENV_TOKENS.get('TECH_SUPPORT_EMAIL', TECH_SUPPORT_EMAIL)

for name, value in ENV_TOKENS.get("CODE_JAIL", {}).items():
    oldvalue = CODE_JAIL.get(name)
    if isinstance(oldvalue, dict):
        for subname, subvalue in value.items():
            oldvalue[subname] = subvalue
    else:
        CODE_JAIL[name] = value

COURSES_WITH_UNSAFE_CODE = ENV_TOKENS.get("COURSES_WITH_UNSAFE_CODE", [])

ASSET_IGNORE_REGEX = ENV_TOKENS.get('ASSET_IGNORE_REGEX', ASSET_IGNORE_REGEX)

COMPREHENSIVE_THEME_DIRS = ENV_TOKENS.get('COMPREHENSIVE_THEME_DIRS', COMPREHENSIVE_THEME_DIRS) or []

# COMPREHENSIVE_THEME_LOCALE_PATHS contain the paths to themes locale directories e.g.
# "COMPREHENSIVE_THEME_LOCALE_PATHS" : [
#        "/edx/src/edx-themes/conf/locale"
#    ],
COMPREHENSIVE_THEME_LOCALE_PATHS = ENV_TOKENS.get('COMPREHENSIVE_THEME_LOCALE_PATHS', [])

DEFAULT_SITE_THEME = ENV_TOKENS.get('DEFAULT_SITE_THEME', DEFAULT_SITE_THEME)
ENABLE_COMPREHENSIVE_THEMING = ENV_TOKENS.get('ENABLE_COMPREHENSIVE_THEMING', ENABLE_COMPREHENSIVE_THEMING)

#Timezone overrides
TIME_ZONE = ENV_TOKENS.get('TIME_ZONE', TIME_ZONE)

# Push to LMS overrides
GIT_REPO_EXPORT_DIR = ENV_TOKENS.get('GIT_REPO_EXPORT_DIR', '/edx/var/edxapp/export_course_repos')

# Translation overrides
LANGUAGES = ENV_TOKENS.get('LANGUAGES', LANGUAGES)
LANGUAGE_CODE = ENV_TOKENS.get('LANGUAGE_CODE', LANGUAGE_CODE)
LANGUAGE_COOKIE = ENV_TOKENS.get('LANGUAGE_COOKIE', LANGUAGE_COOKIE)

USE_I18N = ENV_TOKENS.get('USE_I18N', USE_I18N)

ENV_FEATURES = ENV_TOKENS.get('FEATURES', {})
for feature, value in ENV_FEATURES.items():
    FEATURES[feature] = value

# Additional installed apps
for app in ENV_TOKENS.get('ADDL_INSTALLED_APPS', []):
    INSTALLED_APPS.append(app)

WIKI_ENABLED = ENV_TOKENS.get('WIKI_ENABLED', WIKI_ENABLED)

LOGGING = get_logger_config(LOG_DIR,
                            logging_env=ENV_TOKENS['LOGGING_ENV'],
                            debug=False,
                            service_variant=SERVICE_VARIANT)

#theming start:
PLATFORM_NAME = ENV_TOKENS.get('PLATFORM_NAME', PLATFORM_NAME)
PLATFORM_DESCRIPTION = ENV_TOKENS.get('PLATFORM_DESCRIPTION', PLATFORM_DESCRIPTION)
STUDIO_NAME = ENV_TOKENS.get('STUDIO_NAME', STUDIO_NAME)
STUDIO_SHORT_NAME = ENV_TOKENS.get('STUDIO_SHORT_NAME', STUDIO_SHORT_NAME)

# Event Tracking
if "TRACKING_IGNORE_URL_PATTERNS" in ENV_TOKENS:
    TRACKING_IGNORE_URL_PATTERNS = ENV_TOKENS.get("TRACKING_IGNORE_URL_PATTERNS")

# Django CAS external authentication settings
CAS_EXTRA_LOGIN_PARAMS = ENV_TOKENS.get("CAS_EXTRA_LOGIN_PARAMS", None)
if FEATURES.get('AUTH_USE_CAS'):
    CAS_SERVER_URL = ENV_TOKENS.get("CAS_SERVER_URL", None)
    AUTHENTICATION_BACKENDS = [
        'django.contrib.auth.backends.ModelBackend',
        'django_cas.backends.CASBackend',
    ]

    INSTALLED_APPS.append('django_cas')

    MIDDLEWARE_CLASSES.append('django_cas.middleware.CASMiddleware')
    CAS_ATTRIBUTE_CALLBACK = ENV_TOKENS.get('CAS_ATTRIBUTE_CALLBACK', None)
    if CAS_ATTRIBUTE_CALLBACK:
        import importlib
        CAS_USER_DETAILS_RESOLVER = getattr(
            importlib.import_module(CAS_ATTRIBUTE_CALLBACK['module']),
            CAS_ATTRIBUTE_CALLBACK['function']
        )

# Specific setting for the File Upload Service to store media in a bucket.
FILE_UPLOAD_STORAGE_BUCKET_NAME = ENV_TOKENS.get('FILE_UPLOAD_STORAGE_BUCKET_NAME', FILE_UPLOAD_STORAGE_BUCKET_NAME)
FILE_UPLOAD_STORAGE_PREFIX = ENV_TOKENS.get('FILE_UPLOAD_STORAGE_PREFIX', FILE_UPLOAD_STORAGE_PREFIX)

################ SECURE AUTH ITEMS ###############################
# Secret things: passwords, access keys, etc.
with open(CONFIG_ROOT / CONFIG_PREFIX + "auth.json") as auth_file:
    AUTH_TOKENS = json.load(auth_file)

############### XBlock filesystem field config ##########
if 'DJFS' in AUTH_TOKENS and AUTH_TOKENS['DJFS'] is not None:
    DJFS = AUTH_TOKENS['DJFS']
    if 'url_root' in DJFS:
        DJFS['url_root'] = DJFS['url_root'].format(platform_revision=EDX_PLATFORM_REVISION)

EMAIL_HOST_USER = AUTH_TOKENS.get('EMAIL_HOST_USER', EMAIL_HOST_USER)
EMAIL_HOST_PASSWORD = AUTH_TOKENS.get('EMAIL_HOST_PASSWORD', EMAIL_HOST_PASSWORD)

AWS_SES_REGION_NAME = ENV_TOKENS.get('AWS_SES_REGION_NAME', 'us-east-1')
AWS_SES_REGION_ENDPOINT = ENV_TOKENS.get('AWS_SES_REGION_ENDPOINT', 'email.us-east-1.amazonaws.com')

# Note that this is the Studio key for Segment. There is a separate key for the LMS.
CMS_SEGMENT_KEY = AUTH_TOKENS.get('SEGMENT_KEY')

SECRET_KEY = AUTH_TOKENS['SECRET_KEY']

AWS_ACCESS_KEY_ID = AUTH_TOKENS["AWS_ACCESS_KEY_ID"]
if AWS_ACCESS_KEY_ID == "":
    AWS_ACCESS_KEY_ID = None

AWS_SECRET_ACCESS_KEY = AUTH_TOKENS["AWS_SECRET_ACCESS_KEY"]
if AWS_SECRET_ACCESS_KEY == "":
    AWS_SECRET_ACCESS_KEY = None

AWS_STORAGE_BUCKET_NAME = AUTH_TOKENS.get('AWS_STORAGE_BUCKET_NAME', 'edxuploads')

# Disabling querystring auth instructs Boto to exclude the querystring parameters (e.g. signature, access key) it
# normally appends to every returned URL.
AWS_QUERYSTRING_AUTH = AUTH_TOKENS.get('AWS_QUERYSTRING_AUTH', True)

AWS_DEFAULT_ACL = 'private'
AWS_BUCKET_ACL = AWS_DEFAULT_ACL
AWS_QUERYSTRING_EXPIRE = 7 * 24 * 60 * 60  # 7 days
AWS_S3_CUSTOM_DOMAIN = AUTH_TOKENS.get('AWS_S3_CUSTOM_DOMAIN', 'edxuploads.s3.amazonaws.com')

if AUTH_TOKENS.get('DEFAULT_FILE_STORAGE'):
    DEFAULT_FILE_STORAGE = AUTH_TOKENS.get('DEFAULT_FILE_STORAGE')
elif AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
else:
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

COURSE_IMPORT_EXPORT_BUCKET = ENV_TOKENS.get('COURSE_IMPORT_EXPORT_BUCKET', '')

if COURSE_IMPORT_EXPORT_BUCKET:
    COURSE_IMPORT_EXPORT_STORAGE = 'contentstore.storage.ImportExportS3Storage'
else:
    COURSE_IMPORT_EXPORT_STORAGE = DEFAULT_FILE_STORAGE

USER_TASKS_ARTIFACT_STORAGE = COURSE_IMPORT_EXPORT_STORAGE

DATABASES = AUTH_TOKENS['DATABASES']

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

CONTENTSTORE = AUTH_TOKENS['CONTENTSTORE']
DOC_STORE_CONFIG = AUTH_TOKENS['DOC_STORE_CONFIG']
# Datadog for events!
DATADOG = AUTH_TOKENS.get("DATADOG", {})
DATADOG.update(ENV_TOKENS.get("DATADOG", {}))

# TODO: deprecated (compatibility with previous settings)
if 'DATADOG_API' in AUTH_TOKENS:
    DATADOG['api_key'] = AUTH_TOKENS['DATADOG_API']

# Celery Broker
CELERY_ALWAYS_EAGER = ENV_TOKENS.get("CELERY_ALWAYS_EAGER", False)
CELERY_BROKER_TRANSPORT = ENV_TOKENS.get("CELERY_BROKER_TRANSPORT", "")
CELERY_BROKER_HOSTNAME = ENV_TOKENS.get("CELERY_BROKER_HOSTNAME", "")
CELERY_BROKER_VHOST = ENV_TOKENS.get("CELERY_BROKER_VHOST", "")
CELERY_BROKER_USER = AUTH_TOKENS.get("CELERY_BROKER_USER", "")
CELERY_BROKER_PASSWORD = AUTH_TOKENS.get("CELERY_BROKER_PASSWORD", "")

BROKER_URL = "{0}://{1}:{2}@{3}/{4}".format(CELERY_BROKER_TRANSPORT,
                                            CELERY_BROKER_USER,
                                            CELERY_BROKER_PASSWORD,
                                            CELERY_BROKER_HOSTNAME,
                                            CELERY_BROKER_VHOST)
BROKER_USE_SSL = ENV_TOKENS.get('CELERY_BROKER_USE_SSL', False)

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
        if alternate not in CELERY_QUEUES.keys()
    }
)

# Queue to use for updating grades due to grading policy change
POLICY_CHANGE_GRADES_ROUTING_KEY = ENV_TOKENS.get('POLICY_CHANGE_GRADES_ROUTING_KEY', LOW_PRIORITY_QUEUE)

# Event tracking
TRACKING_BACKENDS.update(AUTH_TOKENS.get("TRACKING_BACKENDS", {}))
EVENT_TRACKING_BACKENDS['tracking_logs']['OPTIONS']['backends'].update(AUTH_TOKENS.get("EVENT_TRACKING_BACKENDS", {}))
EVENT_TRACKING_BACKENDS['segmentio']['OPTIONS']['processors'][0]['OPTIONS']['whitelist'].extend(
    AUTH_TOKENS.get("EVENT_TRACKING_SEGMENTIO_EMIT_WHITELIST", []))

VIRTUAL_UNIVERSITIES = ENV_TOKENS.get('VIRTUAL_UNIVERSITIES', [])

##### ACCOUNT LOCKOUT DEFAULT PARAMETERS #####
MAX_FAILED_LOGIN_ATTEMPTS_ALLOWED = ENV_TOKENS.get("MAX_FAILED_LOGIN_ATTEMPTS_ALLOWED", 5)
MAX_FAILED_LOGIN_ATTEMPTS_LOCKOUT_PERIOD_SECS = ENV_TOKENS.get("MAX_FAILED_LOGIN_ATTEMPTS_LOCKOUT_PERIOD_SECS", 15 * 60)

#### PASSWORD POLICY SETTINGS #####
PASSWORD_MIN_LENGTH = ENV_TOKENS.get("PASSWORD_MIN_LENGTH")
PASSWORD_MAX_LENGTH = ENV_TOKENS.get("PASSWORD_MAX_LENGTH")
PASSWORD_COMPLEXITY = ENV_TOKENS.get("PASSWORD_COMPLEXITY", {})
PASSWORD_DICTIONARY_EDIT_DISTANCE_THRESHOLD = ENV_TOKENS.get("PASSWORD_DICTIONARY_EDIT_DISTANCE_THRESHOLD")
PASSWORD_DICTIONARY = ENV_TOKENS.get("PASSWORD_DICTIONARY", [])

### INACTIVITY SETTINGS ####
SESSION_INACTIVITY_TIMEOUT_IN_SECONDS = AUTH_TOKENS.get("SESSION_INACTIVITY_TIMEOUT_IN_SECONDS")

##### X-Frame-Options response header settings #####
X_FRAME_OPTIONS = ENV_TOKENS.get('X_FRAME_OPTIONS', X_FRAME_OPTIONS)

##### ADVANCED_SECURITY_CONFIG #####
ADVANCED_SECURITY_CONFIG = ENV_TOKENS.get('ADVANCED_SECURITY_CONFIG', {})

################ ADVANCED COMPONENT/PROBLEM TYPES ###############

ADVANCED_PROBLEM_TYPES = ENV_TOKENS.get('ADVANCED_PROBLEM_TYPES', ADVANCED_PROBLEM_TYPES)

################ VIDEO UPLOAD PIPELINE ###############

VIDEO_UPLOAD_PIPELINE = ENV_TOKENS.get('VIDEO_UPLOAD_PIPELINE', VIDEO_UPLOAD_PIPELINE)

################ VIDEO IMAGE STORAGE ###############

VIDEO_IMAGE_SETTINGS = ENV_TOKENS.get('VIDEO_IMAGE_SETTINGS', VIDEO_IMAGE_SETTINGS)

################ VIDEO TRANSCRIPTS STORAGE ###############

VIDEO_TRANSCRIPTS_SETTINGS = ENV_TOKENS.get('VIDEO_TRANSCRIPTS_SETTINGS', VIDEO_TRANSCRIPTS_SETTINGS)

################ PUSH NOTIFICATIONS ###############

PARSE_KEYS = AUTH_TOKENS.get("PARSE_KEYS", {})


# Video Caching. Pairing country codes with CDN URLs.
# Example: {'CN': 'http://api.xuetangx.com/edx/video?s3_url='}
VIDEO_CDN_URL = ENV_TOKENS.get('VIDEO_CDN_URL', {})

if FEATURES['ENABLE_COURSEWARE_INDEX'] or FEATURES['ENABLE_LIBRARY_INDEX']:
    # Use ElasticSearch for the search engine
    SEARCH_ENGINE = "search.elastic.ElasticSearchEngine"

ELASTIC_SEARCH_CONFIG = ENV_TOKENS.get('ELASTIC_SEARCH_CONFIG', [{}])

XBLOCK_SETTINGS = ENV_TOKENS.get('XBLOCK_SETTINGS', {})
XBLOCK_SETTINGS.setdefault("VideoDescriptor", {})["licensing_enabled"] = FEATURES.get("LICENSING", False)
XBLOCK_SETTINGS.setdefault("VideoModule", {})['YOUTUBE_API_KEY'] = AUTH_TOKENS.get('YOUTUBE_API_KEY', YOUTUBE_API_KEY)

################# PROCTORING CONFIGURATION ##################

PROCTORING_BACKEND_PROVIDER = AUTH_TOKENS.get("PROCTORING_BACKEND_PROVIDER", PROCTORING_BACKEND_PROVIDER)
PROCTORING_SETTINGS = ENV_TOKENS.get("PROCTORING_SETTINGS", PROCTORING_SETTINGS)

################# MICROSITE ####################
# microsite specific configurations.
MICROSITE_CONFIGURATION = ENV_TOKENS.get('MICROSITE_CONFIGURATION', {})
MICROSITE_ROOT_DIR = path(ENV_TOKENS.get('MICROSITE_ROOT_DIR', ''))
# this setting specify which backend to be used when pulling microsite specific configuration
MICROSITE_BACKEND = ENV_TOKENS.get("MICROSITE_BACKEND", MICROSITE_BACKEND)
# this setting specify which backend to be used when loading microsite specific templates
MICROSITE_TEMPLATE_BACKEND = ENV_TOKENS.get("MICROSITE_TEMPLATE_BACKEND", MICROSITE_TEMPLATE_BACKEND)
# TTL for microsite database template cache
MICROSITE_DATABASE_TEMPLATE_CACHE_TTL = ENV_TOKENS.get(
    "MICROSITE_DATABASE_TEMPLATE_CACHE_TTL", MICROSITE_DATABASE_TEMPLATE_CACHE_TTL
)

############################ OAUTH2 Provider ###################################

# OpenID Connect issuer ID. Normally the URL of the authentication endpoint.
OAUTH_OIDC_ISSUER = ENV_TOKENS['OAUTH_OIDC_ISSUER']

#### JWT configuration ####
JWT_AUTH.update(ENV_TOKENS.get('JWT_AUTH', {}))

######################## CUSTOM COURSES for EDX CONNECTOR ######################
if FEATURES.get('CUSTOM_COURSES_EDX'):
    INSTALLED_APPS.append('openedx.core.djangoapps.ccxcon')

# Partner support link for CMS footer
PARTNER_SUPPORT_EMAIL = ENV_TOKENS.get('PARTNER_SUPPORT_EMAIL', PARTNER_SUPPORT_EMAIL)

# Affiliate cookie tracking
AFFILIATE_COOKIE_NAME = ENV_TOKENS.get('AFFILIATE_COOKIE_NAME', AFFILIATE_COOKIE_NAME)

############## Settings for Studio Context Sensitive Help ##############

HELP_TOKENS_BOOKS = ENV_TOKENS.get('HELP_TOKENS_BOOKS', HELP_TOKENS_BOOKS)

############## Settings for CourseGraph ############################
COURSEGRAPH_JOB_QUEUE = ENV_TOKENS.get('COURSEGRAPH_JOB_QUEUE', LOW_PRIORITY_QUEUE)

########################## Parental controls config  #######################

# The age at which a learner no longer requires parental consent, or None
# if parental consent is never required.
PARENTAL_CONSENT_AGE_LIMIT = ENV_TOKENS.get(
    'PARENTAL_CONSENT_AGE_LIMIT',
    PARENTAL_CONSENT_AGE_LIMIT
)

########################## Extra middleware classes  #######################

# Allow extra middleware classes to be added to the app through configuration.
MIDDLEWARE_CLASSES.extend(ENV_TOKENS.get('EXTRA_MIDDLEWARE_CLASSES', []))

########################## Derive Any Derived Settings  #######################

derive_settings(__name__)
