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
import datetime
import os

import yaml
from django.core.exceptions import ImproperlyConfigured
from edx_django_utils.plugins import add_plugins
from openedx_events.event_bus import merge_producer_configs
from path import Path as path

from openedx.core.djangoapps.plugins.constants import ProjectType, SettingsType
from openedx.core.lib.derived import Derived, derive_settings
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


################################################# PRODUCTION DEFAULTS ################################################
# We configure some defaults (beyond what has already been configured in common.py) before loading the YAML file below.
# DO NOT ADD NEW DEFAULTS HERE! Put any new setting defaults in common.py instead, along with a setting annotation.
# TODO: Move all these defaults into common.py.

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

CELERY_RESULT_BACKEND = 'django-cache'
BROKER_HEARTBEAT = 60.0
BROKER_HEARTBEAT_CHECKRATE = 2
STATIC_ROOT_BASE = None
STATIC_URL_BASE = None
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
COMPREHENSIVE_THEME_LOCALE_PATHS = []
PREPEND_LOCALE_PATHS = []
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
GOOGLE_ANALYTICS_TRACKING_ID = None
GOOGLE_ANALYTICS_LINKEDIN = None
GOOGLE_SITE_VERIFICATION_ID = None
BRANCH_IO_KEY = None
REGISTRATION_CODE_LENGTH = 8
FACEBOOK_API_VERSION = None
FACEBOOK_APP_SECRET = None
FACEBOOK_APP_ID = None
API_ACCESS_MANAGER_EMAIL = None
API_ACCESS_FROM_EMAIL = None
CHAT_COMPLETION_API = ''
CHAT_COMPLETION_API_KEY = ''
OPENAPI_CACHE_TIMEOUT = 60 * 60
MAINTENANCE_BANNER_TEXT = None
DASHBOARD_COURSE_LIMIT = None

# TODO: We believe these were part of the DEPR'd sysadmin dashboard, and can likely be removed.
SSL_AUTH_EMAIL_DOMAIN = "MIT.EDU"
SSL_AUTH_DN_FORMAT_STRING = (
    "/C=US/ST=Massachusetts/O=Massachusetts Institute of Technology/OU=Client CA v1/CN={0}/emailAddress={1}"
)

CC_MERCHANT_NAME = Derived(lambda settings: settings.PLATFORM_NAME)
EMAIL_FILE_PATH = Derived(lambda settings: settings.DATA_DIR / "emails" / "lms")
LMS_INTERNAL_ROOT_URL = Derived(lambda settings: settings.LMS_ROOT_URL)

# This is the domain that is used to set shared cookies between various sub-domains.
# By default, it's set to the same thing as the SESSION_COOKIE_DOMAIN
SHARED_COOKIE_DOMAIN = Derived(lambda settings: settings.SESSION_COOKIE_DOMAIN)

# We want Bulk Email running on the high-priority queue, so we define the
# routing key that points to it. At the moment, the name is the same.
# We have to reset the value here, since we have changed the value of the queue name.
BULK_EMAIL_ROUTING_KEY = Derived(lambda settings: settings.HIGH_PRIORITY_QUEUE)

# We can run smaller jobs on the low priority queue. See note above for why
# we have to reset the value here.
BULK_EMAIL_ROUTING_KEY_SMALL_JOBS = Derived(lambda settings: settings.DEFAULT_PRIORITY_QUEUE)

# Queue to use for expiring old entitlements
ENTITLEMENTS_EXPIRATION_ROUTING_KEY = Derived(lambda settings: settings.DEFAULT_PRIORITY_QUEUE)

# Intentional defaults.
ID_VERIFICATION_SUPPORT_LINK = Derived(lambda settings: settings.SUPPORT_SITE_LINK)
PASSWORD_RESET_SUPPORT_LINK = Derived(lambda settings: settings.SUPPORT_SITE_LINK)
ACTIVATION_EMAIL_SUPPORT_LINK = Derived(lambda settings: settings.SUPPORT_SITE_LINK)
LOGIN_ISSUE_SUPPORT_LINK = Derived(lambda settings: settings.SUPPORT_SITE_LINK)

# Default queues for various routes
GRADES_DOWNLOAD_ROUTING_KEY = Derived(lambda settings: settings.HIGH_MEM_QUEUE)
CREDENTIALS_GENERATION_ROUTING_KEY = Derived(lambda settings: settings.DEFAULT_PRIORITY_QUEUE)
PROGRAM_CERTIFICATES_ROUTING_KEY = Derived(lambda settings: settings.DEFAULT_PRIORITY_QUEUE)
SOFTWARE_SECURE_VERIFICATION_ROUTING_KEY = Derived(lambda settings: settings.HIGH_PRIORITY_QUEUE)

############## OPEN EDX ENTERPRISE SERVICE CONFIGURATION ######################
# The Open edX Enterprise service is currently hosted via the LMS container/process.
# However, for all intents and purposes this service is treated as a standalone IDA.
# These configuration settings are specific to the Enterprise service and you should
# not find references to them within the edx-platform project.

# Publicly-accessible enrollment URL, for use on the client side.
ENTERPRISE_PUBLIC_ENROLLMENT_API_URL = Derived(
    lambda settings: (settings.LMS_ROOT_URL or '') + settings.LMS_ENROLLMENT_API_PATH
)

# Enrollment URL used on the server-side.
ENTERPRISE_ENROLLMENT_API_URL = Derived(
    lambda settings: (settings.LMS_INTERNAL_ROOT_URL or '') + settings.LMS_ENROLLMENT_API_PATH
)

############## ENTERPRISE SERVICE API CLIENT CONFIGURATION ######################
# The LMS communicates with the Enterprise service via the requests.Session() client
# The below environmental settings are utilized by the LMS when interacting with
# the service, and override the default parameters which are defined in common.py


DEFAULT_ENTERPRISE_API_URL = Derived(
    lambda settings: (
        None if settings.LMS_INTERNAL_ROOT_URL is None
        else settings.LMS_INTERNAL_ROOT_URL + '/enterprise/api/v1/'
    )
)
ENTERPRISE_API_URL = DEFAULT_ENTERPRISE_API_URL

DEFAULT_ENTERPRISE_CONSENT_API_URL = Derived(
    lambda settings: (
        None if settings.LMS_INTERNAL_ROOT_URL is None
        else settings.LMS_INTERNAL_ROOT_URL + '/consent/api/v1/'
    )
)
ENTERPRISE_CONSENT_API_URL = DEFAULT_ENTERPRISE_CONSENT_API_URL


#######################################################################################################################

# A file path to a YAML file from which to load configuration overrides for LMS.
CONFIG_FILE = get_env_setting('LMS_CFG')

with codecs.open(CONFIG_FILE, encoding='utf-8') as f:

    # _YAML_TOKENS starts out with the exact contents of the LMS_CFG YAML file.
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

# TODO: This was for backwards compatibility back when installed django-cookie-samesite (not since 2022).
#       The DCS_ version of the setting can be DEPR'd at this point.
SESSION_COOKIE_SAMESITE = DCS_SESSION_COOKIE_SAMESITE

for feature, value in _YAML_TOKENS.get('FEATURES', {}).items():
    FEATURES[feature] = value

ALLOWED_HOSTS = [
    "*",
    _YAML_TOKENS.get('LMS_BASE'),
    FEATURES['PREVIEW_LMS_BASE'],
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
        if alternate not in CELERY_QUEUES.keys()
    }
)

MKTG_URL_LINK_MAP.update(_YAML_TOKENS.get('MKTG_URL_LINK_MAP', {}))

# Timezone overrides
TIME_ZONE = CELERY_TIMEZONE

# Translation overrides
LANGUAGE_DICT = dict(LANGUAGES)

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
    CORS_ORIGIN_ALLOW_ALL = _YAML_TOKENS.get('CORS_ORIGIN_ALLOW_ALL', False)
    CORS_ALLOW_INSECURE = _YAML_TOKENS.get('CORS_ALLOW_INSECURE', False)
    CROSS_DOMAIN_CSRF_COOKIE_DOMAIN = _YAML_TOKENS.get('CROSS_DOMAIN_CSRF_COOKIE_DOMAIN')

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
MODULESTORE = convert_module_store_setting_if_needed(_YAML_TOKENS.get('MODULESTORE', MODULESTORE))

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

    # TODO: Would it be safe to just set this default in common.py, even if ENABLE_THIRD_PARTY_AUTH is False?
    SOCIAL_AUTH_LTI_CONSUMER_SECRETS = _YAML_TOKENS.get('SOCIAL_AUTH_LTI_CONSUMER_SECRETS', {})

    # third_party_auth config moved to ConfigurationModels. This is for data migration only:
    THIRD_PARTY_AUTH_OLD_CONFIG = _YAML_TOKENS.get('THIRD_PARTY_AUTH', None)

    # TODO: This logic is somewhat insane. We're not sure if it's intentional or not. We've left it
    # as-is for strict backwards compatibility, but it's worth revisiting.
    if hours := _YAML_TOKENS.get('THIRD_PARTY_AUTH_SAML_FETCH_PERIOD_HOURS', 24):
        # If we didn't override the value in YAML, OR we overrode it to a truthy value,
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
if FEATURES['ENABLE_OAUTH2_PROVIDER']:
    OAUTH_ENFORCE_SECURE = True
    OAUTH_ENFORCE_CLIENT_SECURE = True
    # Defaults for the following are defined in lms.envs.common
    OAUTH_EXPIRE_DELTA = datetime.timedelta(days=OAUTH_EXPIRE_CONFIDENTIAL_CLIENT_DAYS)
    OAUTH_EXPIRE_DELTA_PUBLIC = datetime.timedelta(days=OAUTH_EXPIRE_PUBLIC_CLIENT_DAYS)

if (
   FEATURES['ENABLE_COURSEWARE_SEARCH'] or
   FEATURES['ENABLE_DASHBOARD_SEARCH'] or
   FEATURES['ENABLE_COURSE_DISCOVERY'] or
   FEATURES['ENABLE_TEAMS']
   ):
    # Use ElasticSearch as the search engine herein
    SEARCH_ENGINE = "search.elastic.ElasticSearchEngine"

# TODO: Once we have successfully upgraded to ES7, switch this back to ELASTIC_SEARCH_CONFIG.
ELASTIC_SEARCH_CONFIG = _YAML_TOKENS.get('ELASTIC_SEARCH_CONFIG_ES7', [{}])

XBLOCK_SETTINGS.setdefault("VideoBlock", {})["licensing_enabled"] = FEATURES["LICENSING"]
XBLOCK_SETTINGS.setdefault("VideoBlock", {})['YOUTUBE_API_KEY'] = YOUTUBE_API_KEY

##### Custom Courses for EdX #####
if FEATURES['CUSTOM_COURSES_EDX']:
    INSTALLED_APPS += ['lms.djangoapps.ccx', 'openedx.core.djangoapps.ccxcon.apps.CCXConnectorConfig']
    MODULESTORE_FIELD_OVERRIDE_PROVIDERS += (
        'lms.djangoapps.ccx.overrides.CustomCoursesForEdxOverrideProvider',
    )

FIELD_OVERRIDE_PROVIDERS = tuple(FIELD_OVERRIDE_PROVIDERS)

##### Individual Due Date Extensions #####
if FEATURES['INDIVIDUAL_DUE_DATES']:
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

##### Credit Provider Integration #####

##################### LTI Provider #####################
if FEATURES['ENABLE_LTI_PROVIDER']:
    INSTALLED_APPS.append('lms.djangoapps.lti_provider.apps.LtiProviderConfig')
    AUTHENTICATION_BACKENDS.append('lms.djangoapps.lti_provider.users.LtiBackend')

##################### Credit Provider help link ####################

#### JWT configuration ####
JWT_AUTH.update(_YAML_TOKENS.get('JWT_AUTH', {}))


############## ENTERPRISE SERVICE LMS CONFIGURATION ##################################
# The LMS has some features embedded that are related to the Enterprise service, but
# which are not provided by the Enterprise service. These settings override the
# base values for the parameters as defined in common.py

ENTERPRISE_EXCLUDED_REGISTRATION_FIELDS = set(ENTERPRISE_EXCLUDED_REGISTRATION_FIELDS)

########################## Extra middleware classes  #######################

# Allow extra middleware classes to be added to the app through configuration.
MIDDLEWARE.extend(_YAML_TOKENS.get('EXTRA_MIDDLEWARE_CLASSES', []))

########################## Derive Any Derived Settings  #######################

derive_settings(__name__)

############################### Plugin Settings ###############################

# This is at the bottom because it is going to load more settings after base settings are loaded

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
add_plugins(__name__, ProjectType.LMS, SettingsType.PRODUCTION)


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

############## XBlock extra mixins ############################
XBLOCK_MIXINS += tuple(XBLOCK_EXTRA_MIXINS)

############## DRF overrides ##############
REST_FRAMEWORK.update(_YAML_TOKENS.get('REST_FRAMEWORK', {}))

############################# CELERY ############################
CELERY_IMPORTS.extend(_YAML_TOKENS.get('CELERY_EXTRA_IMPORTS', []))

# keys for  big blue button live provider
# TODO: This should not be in the core platform. If it has to stay for now, though, then we should move these
#       defaults into common.py
COURSE_LIVE_GLOBAL_CREDENTIALS["BIG_BLUE_BUTTON"] = {
    "KEY": _YAML_TOKENS.get('BIG_BLUE_BUTTON_GLOBAL_KEY'),
    "SECRET": _YAML_TOKENS.get('BIG_BLUE_BUTTON_GLOBAL_SECRET'),
    "URL": _YAML_TOKENS.get('BIG_BLUE_BUTTON_GLOBAL_URL'),
}

############## Event bus producer ##############
EVENT_BUS_PRODUCER_CONFIG = merge_producer_configs(
    EVENT_BUS_PRODUCER_CONFIG,
    _YAML_TOKENS.get('EVENT_BUS_PRODUCER_CONFIG', {})
)

#####################################################################################################
# HEY! Don't add anything to the end of this file.
# Add your defaults to common.py instead!
# If you really need to add post-YAML logic, add it above the "Derive Any Derived Settings" section.
######################################################################################################
