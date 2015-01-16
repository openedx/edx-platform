"""
This is the default template for our main set of AWS servers. This does NOT
cover the content machines, which use content.py

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

import json

from .common import *
from openedx.core.lib.logsettings import get_logger_config
import os

from path import path
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


################################ ALWAYS THE SAME ##############################

DEBUG = False
TEMPLATE_DEBUG = False

EMAIL_BACKEND = 'django_ses.SESBackend'
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

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
CELERY_RESULT_BACKEND = 'cache'
CELERY_CACHE_BACKEND = 'celery'

# When the broker is behind an ELB, use a heartbeat to refresh the
# connection and to detect if it has been dropped.
BROKER_HEARTBEAT = 10.0
BROKER_HEARTBEAT_CHECKRATE = 2

# Each worker should only fetch one message at a time
CELERYD_PREFETCH_MULTIPLIER = 1

# Skip djcelery migrations, since we don't use the database as the broker
SOUTH_MIGRATION_MODULES = {
    'djcelery': 'ignore',
}

# Rename the exchange and queues for each variant

QUEUE_VARIANT = CONFIG_PREFIX.lower()

CELERY_DEFAULT_EXCHANGE = 'edx.{0}core'.format(QUEUE_VARIANT)

HIGH_PRIORITY_QUEUE = 'edx.{0}core.high'.format(QUEUE_VARIANT)
DEFAULT_PRIORITY_QUEUE = 'edx.{0}core.default'.format(QUEUE_VARIANT)
LOW_PRIORITY_QUEUE = 'edx.{0}core.low'.format(QUEUE_VARIANT)
HIGH_MEM_QUEUE = 'edx.{0}core.high_mem'.format(QUEUE_VARIANT)

CELERY_DEFAULT_QUEUE = DEFAULT_PRIORITY_QUEUE
CELERY_DEFAULT_ROUTING_KEY = DEFAULT_PRIORITY_QUEUE

CELERY_QUEUES = {
    HIGH_PRIORITY_QUEUE: {},
    LOW_PRIORITY_QUEUE: {},
    DEFAULT_PRIORITY_QUEUE: {},
    HIGH_MEM_QUEUE: {},
}

# If we're a worker on the high_mem queue, set ourselves to die after processing
# one request to avoid having memory leaks take down the worker server. This env
# var is set in /etc/init/edx-workers.conf -- this should probably be replaced
# with some celery API call to see what queue we started listening to, but I
# don't know what that call is or if it's active at this point in the code.
if os.environ.get('QUEUE') == 'high_mem':
    CELERYD_MAX_TASKS_PER_CHILD = 1


########################## NON-SECURE ENV CONFIG ##############################
# Things like server locations, ports, etc.

with open(CONFIG_ROOT / CONFIG_PREFIX + "env.json") as env_file:
    ENV_TOKENS = json.load(env_file)

# STATIC_ROOT specifies the directory where static files are
# collected
STATIC_ROOT_BASE = ENV_TOKENS.get('STATIC_ROOT_BASE', None)
if STATIC_ROOT_BASE:
    STATIC_ROOT = path(STATIC_ROOT_BASE)


# STATIC_URL_BASE specifies the base url to use for static files
STATIC_URL_BASE = ENV_TOKENS.get('STATIC_URL_BASE', None)
if STATIC_URL_BASE:
    # collectstatic will fail if STATIC_URL is a unicode string
    STATIC_URL = STATIC_URL_BASE.encode('ascii')
    if not STATIC_URL.endswith("/"):
        STATIC_URL += "/"

PLATFORM_NAME = ENV_TOKENS.get('PLATFORM_NAME', PLATFORM_NAME)
# For displaying on the receipt. At Stanford PLATFORM_NAME != MERCHANT_NAME, but PLATFORM_NAME is a fine default
PLATFORM_TWITTER_ACCOUNT = ENV_TOKENS.get('PLATFORM_TWITTER_ACCOUNT', PLATFORM_TWITTER_ACCOUNT)
PLATFORM_FACEBOOK_ACCOUNT = ENV_TOKENS.get('PLATFORM_FACEBOOK_ACCOUNT', PLATFORM_FACEBOOK_ACCOUNT)

# Social media links for the page footer
SOCIAL_MEDIA_FOOTER_URLS = ENV_TOKENS.get('SOCIAL_MEDIA_FOOTER_URLS', SOCIAL_MEDIA_FOOTER_URLS)

CC_MERCHANT_NAME = ENV_TOKENS.get('CC_MERCHANT_NAME', PLATFORM_NAME)
EMAIL_BACKEND = ENV_TOKENS.get('EMAIL_BACKEND', EMAIL_BACKEND)
EMAIL_FILE_PATH = ENV_TOKENS.get('EMAIL_FILE_PATH', None)
EMAIL_HOST = ENV_TOKENS.get('EMAIL_HOST', 'localhost')  # django default is localhost
EMAIL_PORT = ENV_TOKENS.get('EMAIL_PORT', 25)  # django default is 25
EMAIL_USE_TLS = ENV_TOKENS.get('EMAIL_USE_TLS', False)  # django default is False
SITE_NAME = ENV_TOKENS['SITE_NAME']
HTTPS = ENV_TOKENS.get('HTTPS', HTTPS)
SESSION_ENGINE = ENV_TOKENS.get('SESSION_ENGINE', SESSION_ENGINE)
SESSION_COOKIE_DOMAIN = ENV_TOKENS.get('SESSION_COOKIE_DOMAIN')
SESSION_COOKIE_HTTPONLY = ENV_TOKENS.get('SESSION_COOKIE_HTTPONLY', True)
REGISTRATION_EXTRA_FIELDS = ENV_TOKENS.get('REGISTRATION_EXTRA_FIELDS', REGISTRATION_EXTRA_FIELDS)
SESSION_COOKIE_SECURE = ENV_TOKENS.get('SESSION_COOKIE_SECURE', SESSION_COOKIE_SECURE)

CMS_BASE = ENV_TOKENS.get('CMS_BASE', 'studio.edx.org')

# allow for environments to specify what cookie name our login subsystem should use
# this is to fix a bug regarding simultaneous logins between edx.org and edge.edx.org which can
# happen with some browsers (e.g. Firefox)
if ENV_TOKENS.get('SESSION_COOKIE_NAME', None):
    # NOTE, there's a bug in Django (http://bugs.python.org/issue18012) which necessitates this being a str()
    SESSION_COOKIE_NAME = str(ENV_TOKENS.get('SESSION_COOKIE_NAME'))

BOOK_URL = ENV_TOKENS['BOOK_URL']
MEDIA_URL = ENV_TOKENS['MEDIA_URL']
LOG_DIR = ENV_TOKENS['LOG_DIR']

CACHES = ENV_TOKENS['CACHES']
# Cache used for location mapping -- called many times with the same key/value
# in a given request.
if 'loc_cache' not in CACHES:
    CACHES['loc_cache'] = {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'edx_location_mem_cache',
    }

# Email overrides
DEFAULT_FROM_EMAIL = ENV_TOKENS.get('DEFAULT_FROM_EMAIL', DEFAULT_FROM_EMAIL)
DEFAULT_FEEDBACK_EMAIL = ENV_TOKENS.get('DEFAULT_FEEDBACK_EMAIL', DEFAULT_FEEDBACK_EMAIL)
ADMINS = ENV_TOKENS.get('ADMINS', ADMINS)
SERVER_EMAIL = ENV_TOKENS.get('SERVER_EMAIL', SERVER_EMAIL)
TECH_SUPPORT_EMAIL = ENV_TOKENS.get('TECH_SUPPORT_EMAIL', TECH_SUPPORT_EMAIL)
CONTACT_EMAIL = ENV_TOKENS.get('CONTACT_EMAIL', CONTACT_EMAIL)
BUGS_EMAIL = ENV_TOKENS.get('BUGS_EMAIL', BUGS_EMAIL)
PAYMENT_SUPPORT_EMAIL = ENV_TOKENS.get('PAYMENT_SUPPORT_EMAIL', PAYMENT_SUPPORT_EMAIL)
FINANCE_EMAIL = ENV_TOKENS.get('FINANCE_EMAIL', FINANCE_EMAIL)
UNIVERSITY_EMAIL = ENV_TOKENS.get('UNIVERSITY_EMAIL', UNIVERSITY_EMAIL)
PRESS_EMAIL = ENV_TOKENS.get('PRESS_EMAIL', PRESS_EMAIL)

# Currency
PAID_COURSE_REGISTRATION_CURRENCY = ENV_TOKENS.get('PAID_COURSE_REGISTRATION_CURRENCY',
                                                   PAID_COURSE_REGISTRATION_CURRENCY)

# Payment Report Settings
PAYMENT_REPORT_GENERATOR_GROUP = ENV_TOKENS.get('PAYMENT_REPORT_GENERATOR_GROUP', PAYMENT_REPORT_GENERATOR_GROUP)

# Bulk Email overrides
BULK_EMAIL_DEFAULT_FROM_EMAIL = ENV_TOKENS.get('BULK_EMAIL_DEFAULT_FROM_EMAIL', BULK_EMAIL_DEFAULT_FROM_EMAIL)
BULK_EMAIL_EMAILS_PER_TASK = ENV_TOKENS.get('BULK_EMAIL_EMAILS_PER_TASK', BULK_EMAIL_EMAILS_PER_TASK)
BULK_EMAIL_DEFAULT_RETRY_DELAY = ENV_TOKENS.get('BULK_EMAIL_DEFAULT_RETRY_DELAY', BULK_EMAIL_DEFAULT_RETRY_DELAY)
BULK_EMAIL_MAX_RETRIES = ENV_TOKENS.get('BULK_EMAIL_MAX_RETRIES', BULK_EMAIL_MAX_RETRIES)
BULK_EMAIL_INFINITE_RETRY_CAP = ENV_TOKENS.get('BULK_EMAIL_INFINITE_RETRY_CAP', BULK_EMAIL_INFINITE_RETRY_CAP)
BULK_EMAIL_LOG_SENT_EMAILS = ENV_TOKENS.get('BULK_EMAIL_LOG_SENT_EMAILS', BULK_EMAIL_LOG_SENT_EMAILS)
BULK_EMAIL_RETRY_DELAY_BETWEEN_SENDS = ENV_TOKENS.get('BULK_EMAIL_RETRY_DELAY_BETWEEN_SENDS', BULK_EMAIL_RETRY_DELAY_BETWEEN_SENDS)
# We want Bulk Email running on the high-priority queue, so we define the
# routing key that points to it.  At the moment, the name is the same.
# We have to reset the value here, since we have changed the value of the queue name.
BULK_EMAIL_ROUTING_KEY = HIGH_PRIORITY_QUEUE

# Theme overrides
THEME_NAME = ENV_TOKENS.get('THEME_NAME', None)

# Marketing link overrides
MKTG_URL_LINK_MAP.update(ENV_TOKENS.get('MKTG_URL_LINK_MAP', {}))


# Mobile store URL overrides
MOBILE_STORE_URLS = ENV_TOKENS.get('MOBILE_STORE_URLS', MOBILE_STORE_URLS)

# Timezone overrides
TIME_ZONE = ENV_TOKENS.get('TIME_ZONE', TIME_ZONE)

# Translation overrides
LANGUAGES = ENV_TOKENS.get('LANGUAGES', LANGUAGES)
LANGUAGE_DICT = dict(LANGUAGES)
LANGUAGE_CODE = ENV_TOKENS.get('LANGUAGE_CODE', LANGUAGE_CODE)
USE_I18N = ENV_TOKENS.get('USE_I18N', USE_I18N)

# Additional installed apps
for app in ENV_TOKENS.get('ADDL_INSTALLED_APPS', []):
    INSTALLED_APPS += (app,)

ENV_FEATURES = ENV_TOKENS.get('FEATURES', ENV_TOKENS.get('MITX_FEATURES', {}))
for feature, value in ENV_FEATURES.items():
    FEATURES[feature] = value

WIKI_ENABLED = ENV_TOKENS.get('WIKI_ENABLED', WIKI_ENABLED)
local_loglevel = ENV_TOKENS.get('LOCAL_LOGLEVEL', 'INFO')

LOGGING = get_logger_config(LOG_DIR,
                            logging_env=ENV_TOKENS['LOGGING_ENV'],
                            local_loglevel=local_loglevel,
                            debug=False,
                            service_variant=SERVICE_VARIANT)

COURSE_LISTINGS = ENV_TOKENS.get('COURSE_LISTINGS', {})
SUBDOMAIN_BRANDING = ENV_TOKENS.get('SUBDOMAIN_BRANDING', {})
VIRTUAL_UNIVERSITIES = ENV_TOKENS.get('VIRTUAL_UNIVERSITIES', [])
META_UNIVERSITIES = ENV_TOKENS.get('META_UNIVERSITIES', {})
COMMENTS_SERVICE_URL = ENV_TOKENS.get("COMMENTS_SERVICE_URL", '')
COMMENTS_SERVICE_KEY = ENV_TOKENS.get("COMMENTS_SERVICE_KEY", '')
CERT_QUEUE = ENV_TOKENS.get("CERT_QUEUE", 'test-pull')
ZENDESK_URL = ENV_TOKENS.get("ZENDESK_URL")
FEEDBACK_SUBMISSION_EMAIL = ENV_TOKENS.get("FEEDBACK_SUBMISSION_EMAIL")
MKTG_URLS = ENV_TOKENS.get('MKTG_URLS', MKTG_URLS)

# git repo loading  environment
GIT_REPO_DIR = ENV_TOKENS.get('GIT_REPO_DIR', '/edx/var/edxapp/course_repos')
GIT_IMPORT_STATIC = ENV_TOKENS.get('GIT_IMPORT_STATIC', True)

for name, value in ENV_TOKENS.get("CODE_JAIL", {}).items():
    oldvalue = CODE_JAIL.get(name)
    if isinstance(oldvalue, dict):
        for subname, subvalue in value.items():
            oldvalue[subname] = subvalue
    else:
        CODE_JAIL[name] = value

COURSES_WITH_UNSAFE_CODE = ENV_TOKENS.get("COURSES_WITH_UNSAFE_CODE", [])

ASSET_IGNORE_REGEX = ENV_TOKENS.get('ASSET_IGNORE_REGEX', ASSET_IGNORE_REGEX)

# Event Tracking
if "TRACKING_IGNORE_URL_PATTERNS" in ENV_TOKENS:
    TRACKING_IGNORE_URL_PATTERNS = ENV_TOKENS.get("TRACKING_IGNORE_URL_PATTERNS")

# SSL external authentication settings
SSL_AUTH_EMAIL_DOMAIN = ENV_TOKENS.get("SSL_AUTH_EMAIL_DOMAIN", "MIT.EDU")
SSL_AUTH_DN_FORMAT_STRING = ENV_TOKENS.get("SSL_AUTH_DN_FORMAT_STRING",
                                           "/C=US/ST=Massachusetts/O=Massachusetts Institute of Technology/OU=Client CA v1/CN={0}/emailAddress={1}")

# Django CAS external authentication settings
CAS_EXTRA_LOGIN_PARAMS = ENV_TOKENS.get("CAS_EXTRA_LOGIN_PARAMS", None)
if FEATURES.get('AUTH_USE_CAS'):
    CAS_SERVER_URL = ENV_TOKENS.get("CAS_SERVER_URL", None)
    AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend',
        'django_cas.backends.CASBackend',
    )
    INSTALLED_APPS += ('django_cas',)
    MIDDLEWARE_CLASSES += ('django_cas.middleware.CASMiddleware',)
    CAS_ATTRIBUTE_CALLBACK = ENV_TOKENS.get('CAS_ATTRIBUTE_CALLBACK', None)
    if CAS_ATTRIBUTE_CALLBACK:
        import importlib
        CAS_USER_DETAILS_RESOLVER = getattr(
            importlib.import_module(CAS_ATTRIBUTE_CALLBACK['module']),
            CAS_ATTRIBUTE_CALLBACK['function']
        )

# Video Caching. Pairing country codes with CDN URLs.
# Example: {'CN': 'http://api.xuetangx.com/edx/video?s3_url='}
VIDEO_CDN_URL = ENV_TOKENS.get('VIDEO_CDN_URL', {})

############# CORS headers for cross-domain requests #################

if FEATURES.get('ENABLE_CORS_HEADERS') or FEATURES.get('ENABLE_CROSS_DOMAIN_CSRF_COOKIE'):
    CORS_ALLOW_CREDENTIALS = True
    CORS_ORIGIN_WHITELIST = ENV_TOKENS.get('CORS_ORIGIN_WHITELIST', ())
    CORS_ORIGIN_ALLOW_ALL = ENV_TOKENS.get('CORS_ORIGIN_ALLOW_ALL', False)
    CORS_ALLOW_INSECURE = ENV_TOKENS.get('CORS_ALLOW_INSECURE', False)

    # If setting a cross-domain cookie, it's really important to choose
    # a name for the cookie that is DIFFERENT than the cookies used
    # by each subdomain.  For example, suppose the applications
    # at these subdomains are configured to use the following cookie names:
    #
    # 1) foo.example.com --> "csrftoken"
    # 2) baz.example.com --> "csrftoken"
    # 3) bar.example.com --> "csrftoken"
    #
    # For the cross-domain version of the CSRF cookie, you need to choose
    # a name DIFFERENT than "csrftoken"; otherwise, the new token configured
    # for ".example.com" could conflict with the other cookies,
    # non-deterministically causing 403 responses.
    #
    # Because of the way Django stores cookies, the cookie name MUST
    # be a `str`, not unicode.  Otherwise there will `TypeError`s will be raised
    # when Django tries to call the unicode `translate()` method with the wrong
    # number of parameters.
    CROSS_DOMAIN_CSRF_COOKIE_NAME = str(ENV_TOKENS.get('CROSS_DOMAIN_CSRF_COOKIE_NAME'))

    # When setting the domain for the "cross-domain" version of the CSRF
    # cookie, you should choose something like: ".example.com"
    # (note the leading dot), where both the referer and the host
    # are subdomains of "example.com".
    #
    # Browser security rules require that
    # the cookie domain matches the domain of the server; otherwise
    # the cookie won't get set.  And once the cookie gets set, the client
    # needs to be on a domain that matches the cookie domain, otherwise
    # the client won't be able to read the cookie.
    CROSS_DOMAIN_CSRF_COOKIE_DOMAIN = ENV_TOKENS.get('CROSS_DOMAIN_CSRF_COOKIE_DOMAIN')


# Field overrides.  To use the IDDE feature, add
# 'courseware.student_field_overrides.IndividualStudentOverrideProvider'.
FIELD_OVERRIDE_PROVIDERS = tuple(ENV_TOKENS.get('FIELD_OVERRIDE_PROVIDERS', []))

############################## SECURE AUTH ITEMS ###############
# Secret things: passwords, access keys, etc.

with open(CONFIG_ROOT / CONFIG_PREFIX + "auth.json") as auth_file:
    AUTH_TOKENS = json.load(auth_file)

############### XBlock filesystem field config ##########
if 'DJFS' in AUTH_TOKENS and AUTH_TOKENS['DJFS'] is not None:
    DJFS = AUTH_TOKENS['DJFS']

############### Module Store Items ##########
HOSTNAME_MODULESTORE_DEFAULT_MAPPINGS = ENV_TOKENS.get('HOSTNAME_MODULESTORE_DEFAULT_MAPPINGS', {})

############### Mixed Related(Secure/Not-Secure) Items ##########
# If Segment.io key specified, load it and enable Segment.io if the feature flag is set
SEGMENT_IO_LMS_KEY = AUTH_TOKENS.get('SEGMENT_IO_LMS_KEY')
if SEGMENT_IO_LMS_KEY:
    FEATURES['SEGMENT_IO_LMS'] = ENV_TOKENS.get('SEGMENT_IO_LMS', False)

CC_PROCESSOR_NAME = AUTH_TOKENS.get('CC_PROCESSOR_NAME', CC_PROCESSOR_NAME)
CC_PROCESSOR = AUTH_TOKENS.get('CC_PROCESSOR', CC_PROCESSOR)

SECRET_KEY = AUTH_TOKENS['SECRET_KEY']

AWS_ACCESS_KEY_ID = AUTH_TOKENS["AWS_ACCESS_KEY_ID"]
if AWS_ACCESS_KEY_ID == "":
    AWS_ACCESS_KEY_ID = None

AWS_SECRET_ACCESS_KEY = AUTH_TOKENS["AWS_SECRET_ACCESS_KEY"]
if AWS_SECRET_ACCESS_KEY == "":
    AWS_SECRET_ACCESS_KEY = None

AWS_STORAGE_BUCKET_NAME = AUTH_TOKENS.get('AWS_STORAGE_BUCKET_NAME', 'edxuploads')

# Specific setting for the File Upload Service to store media in a bucket.
FILE_UPLOAD_STORAGE_BUCKET_NAME = ENV_TOKENS.get('FILE_UPLOAD_STORAGE_BUCKET_NAME', FILE_UPLOAD_STORAGE_BUCKET_NAME)
FILE_UPLOAD_STORAGE_PREFIX = ENV_TOKENS.get('FILE_UPLOAD_STORAGE_PREFIX', FILE_UPLOAD_STORAGE_PREFIX)

# If there is a database called 'read_replica', you can use the use_read_replica_if_available
# function in util/query.py, which is useful for very large database reads
DATABASES = AUTH_TOKENS['DATABASES']

XQUEUE_INTERFACE = AUTH_TOKENS['XQUEUE_INTERFACE']

# Get the MODULESTORE from auth.json, but if it doesn't exist,
# use the one from common.py
MODULESTORE = convert_module_store_setting_if_needed(AUTH_TOKENS.get('MODULESTORE', MODULESTORE))
CONTENTSTORE = AUTH_TOKENS.get('CONTENTSTORE', CONTENTSTORE)
DOC_STORE_CONFIG = AUTH_TOKENS.get('DOC_STORE_CONFIG', DOC_STORE_CONFIG)
MONGODB_LOG = AUTH_TOKENS.get('MONGODB_LOG', {})

OPEN_ENDED_GRADING_INTERFACE = AUTH_TOKENS.get('OPEN_ENDED_GRADING_INTERFACE',
                                               OPEN_ENDED_GRADING_INTERFACE)

EMAIL_HOST_USER = AUTH_TOKENS.get('EMAIL_HOST_USER', '')  # django default is ''
EMAIL_HOST_PASSWORD = AUTH_TOKENS.get('EMAIL_HOST_PASSWORD', '')  # django default is ''

# Datadog for events!
DATADOG = AUTH_TOKENS.get("DATADOG", {})
DATADOG.update(ENV_TOKENS.get("DATADOG", {}))

# TODO: deprecated (compatibility with previous settings)
if 'DATADOG_API' in AUTH_TOKENS:
    DATADOG['api_key'] = AUTH_TOKENS['DATADOG_API']

# Analytics dashboard server
ANALYTICS_SERVER_URL = ENV_TOKENS.get("ANALYTICS_SERVER_URL")
ANALYTICS_API_KEY = AUTH_TOKENS.get("ANALYTICS_API_KEY", "")

# Analytics data source
ANALYTICS_DATA_URL = ENV_TOKENS.get("ANALYTICS_DATA_URL", ANALYTICS_DATA_URL)
ANALYTICS_DATA_TOKEN = AUTH_TOKENS.get("ANALYTICS_DATA_TOKEN", ANALYTICS_DATA_TOKEN)

# Analytics Dashboard
ANALYTICS_DASHBOARD_URL = ENV_TOKENS.get("ANALYTICS_DASHBOARD_URL", ANALYTICS_DASHBOARD_URL)
ANALYTICS_DASHBOARD_NAME = ENV_TOKENS.get("ANALYTICS_DASHBOARD_NAME", PLATFORM_NAME + " Insights")

# Zendesk
ZENDESK_USER = AUTH_TOKENS.get("ZENDESK_USER")
ZENDESK_API_KEY = AUTH_TOKENS.get("ZENDESK_API_KEY")

# API Key for inbound requests from Notifier service
EDX_API_KEY = AUTH_TOKENS.get("EDX_API_KEY")

# Celery Broker
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

# upload limits
STUDENT_FILEUPLOAD_MAX_SIZE = ENV_TOKENS.get("STUDENT_FILEUPLOAD_MAX_SIZE", STUDENT_FILEUPLOAD_MAX_SIZE)

# Event tracking
TRACKING_BACKENDS.update(AUTH_TOKENS.get("TRACKING_BACKENDS", {}))
EVENT_TRACKING_BACKENDS.update(AUTH_TOKENS.get("EVENT_TRACKING_BACKENDS", {}))
TRACKING_SEGMENTIO_WEBHOOK_SECRET = AUTH_TOKENS.get(
    "TRACKING_SEGMENTIO_WEBHOOK_SECRET",
    TRACKING_SEGMENTIO_WEBHOOK_SECRET
)
TRACKING_SEGMENTIO_ALLOWED_TYPES = ENV_TOKENS.get("TRACKING_SEGMENTIO_ALLOWED_TYPES", TRACKING_SEGMENTIO_ALLOWED_TYPES)
TRACKING_SEGMENTIO_DISALLOWED_SUBSTRING_NAMES = ENV_TOKENS.get(
    "TRACKING_SEGMENTIO_DISALLOWED_SUBSTRING_NAMES",
    TRACKING_SEGMENTIO_DISALLOWED_SUBSTRING_NAMES
)
TRACKING_SEGMENTIO_SOURCE_MAP = ENV_TOKENS.get("TRACKING_SEGMENTIO_SOURCE_MAP", TRACKING_SEGMENTIO_SOURCE_MAP)

# Student identity verification settings
VERIFY_STUDENT = AUTH_TOKENS.get("VERIFY_STUDENT", VERIFY_STUDENT)

# Grades download
GRADES_DOWNLOAD_ROUTING_KEY = HIGH_MEM_QUEUE

GRADES_DOWNLOAD = ENV_TOKENS.get("GRADES_DOWNLOAD", GRADES_DOWNLOAD)

##### ORA2 ######
# Prefix for uploads of example-based assessment AI classifiers
# This can be used to separate uploads for different environments
# within the same S3 bucket.
ORA2_FILE_PREFIX = ENV_TOKENS.get("ORA2_FILE_PREFIX", ORA2_FILE_PREFIX)

##### ACCOUNT LOCKOUT DEFAULT PARAMETERS #####
MAX_FAILED_LOGIN_ATTEMPTS_ALLOWED = ENV_TOKENS.get("MAX_FAILED_LOGIN_ATTEMPTS_ALLOWED", 5)
MAX_FAILED_LOGIN_ATTEMPTS_LOCKOUT_PERIOD_SECS = ENV_TOKENS.get("MAX_FAILED_LOGIN_ATTEMPTS_LOCKOUT_PERIOD_SECS", 15 * 60)

MICROSITE_CONFIGURATION = ENV_TOKENS.get('MICROSITE_CONFIGURATION', {})
MICROSITE_ROOT_DIR = path(ENV_TOKENS.get('MICROSITE_ROOT_DIR', ''))

#### PASSWORD POLICY SETTINGS #####
PASSWORD_MIN_LENGTH = ENV_TOKENS.get("PASSWORD_MIN_LENGTH")
PASSWORD_MAX_LENGTH = ENV_TOKENS.get("PASSWORD_MAX_LENGTH")
PASSWORD_COMPLEXITY = ENV_TOKENS.get("PASSWORD_COMPLEXITY", {})
PASSWORD_DICTIONARY_EDIT_DISTANCE_THRESHOLD = ENV_TOKENS.get("PASSWORD_DICTIONARY_EDIT_DISTANCE_THRESHOLD")
PASSWORD_DICTIONARY = ENV_TOKENS.get("PASSWORD_DICTIONARY", [])

### INACTIVITY SETTINGS ####
SESSION_INACTIVITY_TIMEOUT_IN_SECONDS = AUTH_TOKENS.get("SESSION_INACTIVITY_TIMEOUT_IN_SECONDS")

##### LMS DEADLINE DISPLAY TIME_ZONE #######
TIME_ZONE_DISPLAYED_FOR_DEADLINES = ENV_TOKENS.get("TIME_ZONE_DISPLAYED_FOR_DEADLINES",
                                                   TIME_ZONE_DISPLAYED_FOR_DEADLINES)

##### X-Frame-Options response header settings #####
X_FRAME_OPTIONS = ENV_TOKENS.get('X_FRAME_OPTIONS', X_FRAME_OPTIONS)

##### Third-party auth options ################################################
THIRD_PARTY_AUTH = AUTH_TOKENS.get('THIRD_PARTY_AUTH', THIRD_PARTY_AUTH)

##### OAUTH2 Provider ##############
if FEATURES.get('ENABLE_OAUTH2_PROVIDER'):
    OAUTH_OIDC_ISSUER = ENV_TOKENS['OAUTH_OIDC_ISSUER']
    OAUTH_ENFORCE_SECURE = ENV_TOKENS.get('OAUTH_ENFORCE_SECURE', True)
    OAUTH_ENFORCE_CLIENT_SECURE = ENV_TOKENS.get('OAUTH_ENFORCE_CLIENT_SECURE', True)

##### ADVANCED_SECURITY_CONFIG #####
ADVANCED_SECURITY_CONFIG = ENV_TOKENS.get('ADVANCED_SECURITY_CONFIG', {})

##### GOOGLE ANALYTICS IDS #####
GOOGLE_ANALYTICS_ACCOUNT = AUTH_TOKENS.get('GOOGLE_ANALYTICS_ACCOUNT')
GOOGLE_ANALYTICS_LINKEDIN = AUTH_TOKENS.get('GOOGLE_ANALYTICS_LINKEDIN')

##### OPTIMIZELY PROJECT ID #####
OPTIMIZELY_PROJECT_ID = AUTH_TOKENS.get('OPTIMIZELY_PROJECT_ID', OPTIMIZELY_PROJECT_ID)

#### Course Registration Code length ####
REGISTRATION_CODE_LENGTH = ENV_TOKENS.get('REGISTRATION_CODE_LENGTH', 8)

# REGISTRATION CODES DISPLAY INFORMATION
INVOICE_CORP_ADDRESS = ENV_TOKENS.get('INVOICE_CORP_ADDRESS', INVOICE_CORP_ADDRESS)
INVOICE_PAYMENT_INSTRUCTIONS = ENV_TOKENS.get('INVOICE_PAYMENT_INSTRUCTIONS', INVOICE_PAYMENT_INSTRUCTIONS)

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

#date format the api will be formatting the datetime values
API_DATE_FORMAT = '%Y-%m-%d'
API_DATE_FORMAT = ENV_TOKENS.get('API_DATE_FORMAT', API_DATE_FORMAT)

# Enrollment API Cache Timeout
ENROLLMENT_COURSE_DETAILS_CACHE_TIMEOUT = ENV_TOKENS.get('ENROLLMENT_COURSE_DETAILS_CACHE_TIMEOUT', 60)

# PDF RECEIPT/INVOICE OVERRIDES
PDF_RECEIPT_TAX_ID = ENV_TOKENS.get('PDF_RECEIPT_TAX_ID', PDF_RECEIPT_TAX_ID)
PDF_RECEIPT_FOOTER_TEXT = ENV_TOKENS.get('PDF_RECEIPT_FOOTER_TEXT', PDF_RECEIPT_FOOTER_TEXT)
PDF_RECEIPT_DISCLAIMER_TEXT = ENV_TOKENS.get('PDF_RECEIPT_DISCLAIMER_TEXT', PDF_RECEIPT_DISCLAIMER_TEXT)
PDF_RECEIPT_BILLING_ADDRESS = ENV_TOKENS.get('PDF_RECEIPT_BILLING_ADDRESS', PDF_RECEIPT_BILLING_ADDRESS)
PDF_RECEIPT_TERMS_AND_CONDITIONS = ENV_TOKENS.get('PDF_RECEIPT_TERMS_AND_CONDITIONS', PDF_RECEIPT_TERMS_AND_CONDITIONS)
PDF_RECEIPT_TAX_ID_LABEL = ENV_TOKENS.get('PDF_RECEIPT_TAX_ID_LABEL', PDF_RECEIPT_TAX_ID_LABEL)
PDF_RECEIPT_LOGO_PATH = ENV_TOKENS.get('PDF_RECEIPT_LOGO_PATH', PDF_RECEIPT_LOGO_PATH)
PDF_RECEIPT_COBRAND_LOGO_PATH = ENV_TOKENS.get('PDF_RECEIPT_COBRAND_LOGO_PATH', PDF_RECEIPT_COBRAND_LOGO_PATH)
PDF_RECEIPT_LOGO_HEIGHT_MM = ENV_TOKENS.get('PDF_RECEIPT_LOGO_HEIGHT_MM', PDF_RECEIPT_LOGO_HEIGHT_MM)
PDF_RECEIPT_COBRAND_LOGO_HEIGHT_MM = ENV_TOKENS.get(
    'PDF_RECEIPT_COBRAND_LOGO_HEIGHT_MM', PDF_RECEIPT_COBRAND_LOGO_HEIGHT_MM
)

if FEATURES.get('ENABLE_COURSEWARE_SEARCH'):
    # Use ElasticSearch as the search engine herein
    SEARCH_ENGINE = "search.elastic.ElasticSearchEngine"

# Facebook app
FACEBOOK_API_VERSION = AUTH_TOKENS.get("FACEBOOK_API_VERSION")
FACEBOOK_APP_SECRET = AUTH_TOKENS.get("FACEBOOK_APP_SECRET")
FACEBOOK_APP_ID = AUTH_TOKENS.get("FACEBOOK_APP_ID")

XBLOCK_SETTINGS = ENV_TOKENS.get('XBLOCK_SETTINGS', {})

##### CDN EXPERIMENT/MONITORING FLAGS #####
CDN_VIDEO_URLS = ENV_TOKENS.get('CDN_VIDEO_URLS', CDN_VIDEO_URLS)
ONLOAD_BEACON_SAMPLE_RATE = ENV_TOKENS.get('ONLOAD_BEACON_SAMPLE_RATE', ONLOAD_BEACON_SAMPLE_RATE)

##### ECOMMERCE API CONFIGURATION SETTINGS #####
ECOMMERCE_API_URL = ENV_TOKENS.get('ECOMMERCE_API_URL', ECOMMERCE_API_URL)
ECOMMERCE_API_SIGNING_KEY = AUTH_TOKENS.get('ECOMMERCE_API_SIGNING_KEY', ECOMMERCE_API_SIGNING_KEY)
ECOMMERCE_API_TIMEOUT = ENV_TOKENS.get('ECOMMERCE_API_TIMEOUT', ECOMMERCE_API_TIMEOUT)

##### Custom Courses for EdX #####
if FEATURES.get('CUSTOM_COURSES_EDX'):
    INSTALLED_APPS += ('ccx',)
    MIDDLEWARE_CLASSES += ('ccx.overrides.CcxMiddleware',)
    FIELD_OVERRIDE_PROVIDERS += (
        'ccx.overrides.CustomCoursesForEdxOverrideProvider',
    )

##### Individual Due Date Extensions #####
if FEATURES.get('INDIVIDUAL_DUE_DATES'):
    FIELD_OVERRIDE_PROVIDERS += (
        'courseware.student_field_overrides.IndividualStudentOverrideProvider',
    )
