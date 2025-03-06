"""
Override common.py with key-value pairs from YAML (plus some extra defaults & post-processing).

This file is in the process of being restructured. Please see:
https://github.com/openedx/edx-platform/blob/master/docs/decisions/0022-settings-simplification.rst
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=wildcard-import, unused-wildcard-import


import codecs
import os
import warnings
import yaml

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


#######################################################################################################################
#### PRODUCTION DEFAULTS
####
#### Configure some defaults (beyond what has already been configured in common.py) before loading the YAML file.
#### DO NOT ADD NEW DEFAULTS HERE! Put any new setting defaults in common.py instead, along with a setting annotation.
#### TODO: Move all these defaults into common.py.
####

DEBUG = False

# IMPORTANT: With this enabled, the server must always be behind a proxy that strips the header HTTP_X_FORWARDED_PROTO
# from client requests. Otherwise, a user can fool our server into thinking it was an https connection. See
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header for other warnings.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Constant defaults (alphabetical)
AUTHORING_API_URL = ''
AWS_QUERYSTRING_AUTH = True
AWS_S3_CUSTOM_DOMAIN = 'edxuploads.s3.amazonaws.com'
AWS_STORAGE_BUCKET_NAME = 'edxuploads'
BROKER_HEARTBEAT = 60.0
BROKER_HEARTBEAT_CHECKRATE = 2
CELERY_ALWAYS_EAGER = False
CELERY_BROKER_HOSTNAME = ""
CELERY_BROKER_PASSWORD = ""
CELERY_BROKER_TRANSPORT = ""
CELERY_BROKER_USER = ""
CELERY_RESULT_BACKEND = 'django-cache'
CHAT_COMPLETION_API = ''
CHAT_COMPLETION_API_KEY = ''
CLEAR_REQUEST_CACHE_ON_TASK_COMPLETION = True
CMS_BASE = None
CMS_ROOT_URL = None
DEFAULT_TEMPLATE_ENGINE['OPTIONS']['debug'] = False
IDA_LOGOUT_URI_LIST = []
LEARNER_ENGAGEMENT_PROMPT_FOR_ACTIVE_CONTRACT = ''
LEARNER_ENGAGEMENT_PROMPT_FOR_NON_ACTIVE_CONTRACT = ''
LEARNER_PROGRESS_PROMPT_FOR_ACTIVE_CONTRACT = ''
LEARNER_PROGRESS_PROMPT_FOR_NON_ACTIVE_CONTRACT = ''
LMS_BASE = None
LMS_ROOT_URL = None
OPENAPI_CACHE_TIMEOUT = 60 * 60
PARSE_KEYS = {}
REGISTRATION_EMAIL_PATTERNS_ALLOWED = None
SESSION_COOKIE_DOMAIN = None
SESSION_COOKIE_HTTPONLY = True
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_INACTIVITY_TIMEOUT_IN_SECONDS = None
STATIC_ROOT_BASE = None
STATIC_URL_BASE = None
VIDEO_CDN_URL = {}

# Derived defaults (alphabetical)
BROKER_USE_SSL = Derived(lambda settings: settings.CELERY_BROKER_USE_SSL)
EMAIL_FILE_PATH = Derived(lambda settings: settings.DATA_DIR / "emails" / "studio")
ENTERPRISE_API_URL = Derived(lambda settings: settings.LMS_INTERNAL_ROOT_URL + '/enterprise/api/v1/')
ENTERPRISE_CONSENT_API_URL = Derived(lambda settings: settings.LMS_INTERNAL_ROOT_URL + '/consent/api/v1/')
LMS_INTERNAL_ROOT_URL = Derived(lambda settings: settings.LMS_ROOT_URL)
POLICY_CHANGE_GRADES_ROUTING_KEY = Derived(lambda settings: settings.DEFAULT_PRIORITY_QUEUE)
SCRAPE_YOUTUBE_THUMBNAILS_JOB_QUEUE = Derived(lambda settings: settings.DEFAULT_PRIORITY_QUEUE)
SHARED_COOKIE_DOMAIN = Derived(lambda settings: settings.SESSION_COOKIE_DOMAIN)
SINGLE_LEARNER_COURSE_REGRADE_ROUTING_KEY = Derived(lambda settings: settings.DEFAULT_PRIORITY_QUEUE)
SOFTWARE_SECURE_VERIFICATION_ROUTING_KEY = Derived(lambda settings: settings.HIGH_PRIORITY_QUEUE)
UPDATE_SEARCH_INDEX_JOB_QUEUE = Derived(lambda settings: settings.DEFAULT_PRIORITY_QUEUE)
VIDEO_TRANSCRIPT_MIGRATIONS_JOB_QUEUE = Derived(lambda settings: settings.DEFAULT_PRIORITY_QUEUE)


#######################################################################################################################
#### YAML LOADING
####

# A file path to a YAML file from which to load configuration overrides for LMS.
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

    # _YAML_TOKENS starts out with the exact contents of the CMS_CFG YAML file.
    # Please avoid adding new references to _YAML_TOKENS. Such references make our settings logic more complex.
    # Instead, just reference the Django settings, which we define in the next step...
    _YAML_TOKENS = yaml.safe_load(f)

    # Update the global namespace of this module with the key-value pairs from _YAML_TOKENS.
    # In other words: For (almost) every YAML key-value pair, define/update a Django setting with that name and value.
    vars().update({

        #  Note: If `value` is a mutable object (e.g., a dict), then it will be aliased between the global namespace and
        #  _YAML_TOKENS. In other words, updates to `value` will manifest in _YAML_TOKENS as well. This is intentional,
        #  in order to maintain backwards compatibility with old Django plugins which use _YAML_TOKENS.
        key: value
        for key, value in _YAML_TOKENS.items()

        # Do NOT define/update Django settings for these particular special keys.
        # We handle each of these with its special logic (below, in this same module).
        # For example, we need to *update* the default FEATURES dict rather than wholesale *override* it.
        if key not in [
            'FEATURES',
            'TRACKING_BACKENDS',
            'EVENT_TRACKING_BACKENDS',
            'JWT_AUTH',
            'CELERY_QUEUES',
            'MKTG_URL_LINK_MAP',
            'REST_FRAMEWORK',
            'EVENT_BUS_PRODUCER_CONFIG',
        ]
    })


#######################################################################################################################
#### LOAD THE EDX-PLATFORM GIT REVISION
####

try:
    # A file path to a YAML file from which to load all the code revisions currently deployed
    REVISION_CONFIG_FILE = get_env_setting('REVISION_CFG')

    with codecs.open(REVISION_CONFIG_FILE, encoding='utf-8') as f:
        REVISION_CONFIG = yaml.safe_load(f)
except Exception:  # pylint: disable=broad-except
    REVISION_CONFIG = {}

# Do NOT calculate this dynamically at startup with git because it's *slow*.
EDX_PLATFORM_REVISION = REVISION_CONFIG.get('EDX_PLATFORM_REVISION', EDX_PLATFORM_REVISION)


#######################################################################################################################
#### POST-PROCESSING OF YAML
####
#### This is where we do a bunch of logic to post-process the results of the YAML, including: conditionally setting
#### updates, merging dicts+lists which we did not override, and in some cases simply ignoring the YAML value in favor
#### of a specific production value.
####

# Don't use a connection pool, since connections are dropped by ELB.
BROKER_POOL_LIMIT = 0
BROKER_CONNECTION_TIMEOUT = 1

# Each worker should only fetch one message at a time
CELERYD_PREFETCH_MULTIPLIER = 1

CELERY_ROUTES = "openedx.core.lib.celery.routers.route_task"

if STATIC_URL_BASE:
    STATIC_URL = STATIC_URL_BASE
    if not STATIC_URL.endswith("/"):
        STATIC_URL += "/"
    STATIC_URL += 'studio/'

if STATIC_ROOT_BASE:
    STATIC_ROOT = path(STATIC_ROOT_BASE) / 'studio'
    WEBPACK_LOADER['DEFAULT']['STATS_FILE'] = STATIC_ROOT / "webpack-stats.json"
    WEBPACK_LOADER['WORKERS']['STATS_FILE'] = STATIC_ROOT / "webpack-worker-stats.json"

DATA_DIR = path(DATA_DIR)

ALLOWED_HOSTS = [
    # TODO: bbeggs remove this before prod, temp fix to get load testing running
    "*",
    CMS_BASE,
]

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
STATICFILES_STORAGE = os.environ.get('STATICFILES_STORAGE', STATICFILES_STORAGE)

CSRF_TRUSTED_ORIGINS = _YAML_TOKENS.get("CSRF_TRUSTED_ORIGINS_WITH_SCHEME", [])

MKTG_URL_LINK_MAP.update(_YAML_TOKENS.get('MKTG_URL_LINK_MAP', {}))

#Timezone overrides
TIME_ZONE = CELERY_TIMEZONE

for feature, value in _YAML_TOKENS.get('FEATURES', {}).items():
    FEATURES[feature] = value

# Additional installed apps
for app in _YAML_TOKENS.get('ADDL_INSTALLED_APPS', []):
    INSTALLED_APPS.append(app)

LOGGING = get_logger_config(
    LOG_DIR,
    logging_env=LOGGING_ENV,
    service_variant=SERVICE_VARIANT,
)

LOGIN_REDIRECT_WHITELIST.extend([reverse_lazy('home')])

############### XBlock filesystem field config ##########
if 'url_root' in DJFS:
    DJFS['url_root'] = DJFS['url_root'].format(platform_revision=EDX_PLATFORM_REVISION)

# Note that this is the Studio key for Segment. There is a separate key for the LMS.
CMS_SEGMENT_KEY = _YAML_TOKENS.get('SEGMENT_KEY')

if AWS_ACCESS_KEY_ID == "":
    AWS_ACCESS_KEY_ID = None

if AWS_SECRET_ACCESS_KEY == "":
    AWS_SECRET_ACCESS_KEY = None

AWS_DEFAULT_ACL = 'private'
AWS_BUCKET_ACL = AWS_DEFAULT_ACL
# The number of seconds that a generated URL is valid for.
AWS_QUERYSTRING_EXPIRE = 7 * 24 * 60 * 60  # 7 days

# Change to S3Boto3 if we haven't specified another default storage AND we have specified AWS creds.
if (not _YAML_TOKENS.get('DEFAULT_FILE_STORAGE')) and AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

if COURSE_IMPORT_EXPORT_BUCKET:
    COURSE_IMPORT_EXPORT_STORAGE = 'cms.djangoapps.contentstore.storage.ImportExportS3Storage'
else:
    COURSE_IMPORT_EXPORT_STORAGE = DEFAULT_FILE_STORAGE

USER_TASKS_ARTIFACT_STORAGE = COURSE_IMPORT_EXPORT_STORAGE

if COURSE_METADATA_EXPORT_BUCKET:
    COURSE_METADATA_EXPORT_STORAGE = 'cms.djangoapps.export_course_metadata.storage.CourseMetadataExportS3Storage'
else:
    COURSE_METADATA_EXPORT_STORAGE = DEFAULT_FILE_STORAGE

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

MODULESTORE = convert_module_store_setting_if_needed(MODULESTORE)

# Celery Broker

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

# Build a CELERY_QUEUES dict the way that celery expects, based on a couple lists of queue names from the YAML.
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
        if alternate not in list(CELERY_QUEUES.keys())
    }
)

# Event tracking
TRACKING_BACKENDS.update(_YAML_TOKENS.get("TRACKING_BACKENDS", {}))
EVENT_TRACKING_BACKENDS['tracking_logs']['OPTIONS']['backends'].update(
    _YAML_TOKENS.get("EVENT_TRACKING_BACKENDS", {})
)
EVENT_TRACKING_BACKENDS['segmentio']['OPTIONS']['processors'][0]['OPTIONS']['whitelist'].extend(
    EVENT_TRACKING_SEGMENTIO_EMIT_WHITELIST
)


if FEATURES['ENABLE_COURSEWARE_INDEX'] or FEATURES['ENABLE_LIBRARY_INDEX']:
    # Use ElasticSearch for the search engine
    SEARCH_ENGINE = "search.elastic.ElasticSearchEngine"

# TODO: Once we have successfully upgraded to ES7, switch this back to ELASTIC_SEARCH_CONFIG.
ELASTIC_SEARCH_CONFIG = _YAML_TOKENS.get('ELASTIC_SEARCH_CONFIG_ES7', [{}])

XBLOCK_SETTINGS.setdefault("VideoBlock", {})["licensing_enabled"] = FEATURES["LICENSING"]
XBLOCK_SETTINGS.setdefault("VideoBlock", {})['YOUTUBE_API_KEY'] = YOUTUBE_API_KEY

############################ OAUTH2 Provider ###################################

#### JWT configuration ####
JWT_AUTH.update(_YAML_TOKENS.get('JWT_AUTH', {}))

######################## CUSTOM COURSES for EDX CONNECTOR ######################
if FEATURES['CUSTOM_COURSES_EDX']:
    INSTALLED_APPS.append('openedx.core.djangoapps.ccxcon.apps.CCXConnectorConfig')

########################## Extra middleware classes  #######################

# Allow extra middleware classes to be added to the app through configuration.
MIDDLEWARE.extend(EXTRA_MIDDLEWARE_CLASSES)


#######################################################################################################################
#### DERIVE ANY DERIVED SETTINGS
####

derive_settings(__name__)


#######################################################################################################################
#### LOAD SETTINGS FROM DJANGO PLUGINS
####
#### This is at the bottom because it is going to load more settings after base settings are loaded
####

# These dicts are defined solely for BACKWARDS COMPATIBILITY with existing plugins which may theoretically
# rely upon them. Please do not add new references to these dicts!
# - If you need to access the YAML values in this module, use _YAML_TOKENS.
# - If you need to access to these values elsewhere, use the corresponding rendered `settings.*`
#   value rathering than diving into these dicts.
ENV_TOKENS = _YAML_TOKENS
AUTH_TOKENS = _YAML_TOKENS
ENV_FEATURES = _YAML_TOKENS.get("FEATURES", {})
ENV_CELERY_QUEUES = _YAML_CELERY_QUEUES
ALTERNATE_QUEUE_ENVS = _YAML_ALTERNATE_WORKER_QUEUES

# Load production.py in plugins
add_plugins(__name__, ProjectType.CMS, SettingsType.PRODUCTION)


#######################################################################################################################
#### MORE YAML POST-PROCESSING
####
#### More post-processing, but these will not be available Django plugins.
#### Unclear whether or not these are down here intentionally.
####

############# CORS headers for cross-domain requests #################
if FEATURES['ENABLE_CORS_HEADERS']:
    CORS_ALLOW_CREDENTIALS = True
    CORS_ORIGIN_WHITELIST = _YAML_TOKENS.get('CORS_ORIGIN_WHITELIST', ())
    CORS_ORIGIN_ALLOW_ALL = _YAML_TOKENS.get('CORS_ORIGIN_ALLOW_ALL', False)
    CORS_ALLOW_INSECURE = _YAML_TOKENS.get('CORS_ALLOW_INSECURE', False)

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

############## XBlock extra mixins ############################
XBLOCK_MIXINS += tuple(XBLOCK_EXTRA_MIXINS)

# Translation overrides
LANGUAGE_COOKIE_NAME = _YAML_TOKENS.get('LANGUAGE_COOKIE') or LANGUAGE_COOKIE_NAME

############## DRF overrides ##############
REST_FRAMEWORK.update(_YAML_TOKENS.get('REST_FRAMEWORK', {}))

# keys for  big blue button live provider
# TODO: This should not be in the core platform. If it has to stay for now, though, then we should move these
#       defaults into common.py
COURSE_LIVE_GLOBAL_CREDENTIALS["BIG_BLUE_BUTTON"] = {
    "KEY": _YAML_TOKENS.get('BIG_BLUE_BUTTON_GLOBAL_KEY'),
    "SECRET": _YAML_TOKENS.get('BIG_BLUE_BUTTON_GLOBAL_SECRET'),
    "URL": _YAML_TOKENS.get('BIG_BLUE_BUTTON_GLOBAL_URL'),
}

# TODO: We believe that this could be more simply defined as CMS_ROOT_URL. We are not making the change now,
#       but please don't follow this pattern in other defaults...
INACTIVE_USER_URL = f'http{"s" if HTTPS == "on" else ""}://{CMS_BASE}'

############## Event bus producer ##############
EVENT_BUS_PRODUCER_CONFIG = merge_producer_configs(
    EVENT_BUS_PRODUCER_CONFIG,
    _YAML_TOKENS.get('EVENT_BUS_PRODUCER_CONFIG', {})
)

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


#######################################################################################################################
# HEY! Don't add anything to the end of this file.
# Add your defaults to common.py instead!
# If you really need to add post-YAML logic, add it above the "DERIVE ANY DERIVED SETTINGS" section.
#######################################################################################################################
