# -*- coding: utf-8 -*-

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

import dateutil
import yaml
from corsheaders.defaults import default_headers as corsheaders_default_headers
from django.core.exceptions import ImproperlyConfigured
from path import Path as path

from openedx.core.djangoapps.plugins import plugin_settings, constants as plugin_constants
from openedx.core.lib.derived import derive_settings
from openedx.core.lib.logsettings import get_logger_config
from xmodule.modulestore.modulestore_settings import convert_module_store_setting_if_needed

from .common import *


def get_env_setting(setting):
    """ Get the environment setting or return exception """
    try:
        return os.environ[setting]
    except KeyError:
        error_msg = u"Set the %s env variable" % setting
        raise ImproperlyConfigured(error_msg)

# A file path to a YAML file from which to load all the configuration for the edx platform
CONFIG_FILE = get_env_setting('LMS_CFG')

with codecs.open(CONFIG_FILE, encoding='utf-8') as f:
    __config__ = yaml.safe_load(f)

    # ENV_TOKENS and AUTH_TOKENS are included for reverse compatibility.
    # Removing them may break plugins that rely on them.
    ENV_TOKENS = __config__
    AUTH_TOKENS = __config__

# A file path to a YAML file from which to load all the code revisions currently deployed
REVISION_CONFIG_FILE = get_env_setting('REVISION_CFG')

try:
    with codecs.open(REVISION_CONFIG_FILE, encoding='utf-8') as f:
        REVISION_CONFIG = yaml.safe_load(f)
except Exception:  # pylint: disable=broad-except
    REVISION_CONFIG = {}

# Do NOT calculate this dynamically at startup with git because it's *slow*.
EDX_PLATFORM_REVISION = REVISION_CONFIG.get('EDX_PLATFORM_REVISION', EDX_PLATFORM_REVISION)

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
DEFAULT_TEMPLATE_ENGINE['OPTIONS']['debug'] = False

EMAIL_BACKEND = 'django_ses.SESBackend'
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

# IMPORTANT: With this enabled, the server must always be behind a proxy that
# strips the header HTTP_X_FORWARDED_PROTO from client requests. Otherwise,
# a user can fool our server into thinking it was an https connection.
# See
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
# for other warnings.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

##############################################################################


def s(name, default=None, set_global=True):
    """
    Get a Django setting value from a configuration file and set it globally.
    If setting does not exist in the file, use a default value.

    Returns:
        object: Django setting value
    """
    # if no explicit default is provided as default, use the current global value or None
    if not default:
        if name in globals():
            default = globals()[name]

    # get value from config file if it is provided, default value otherwise
    value = __config__.get(name, default)

    if set_global:
        globals()[name] = value

    return value

###################################### CELERY  ################################

# Don't use a connection pool, since connections are dropped by ELB.
BROKER_POOL_LIMIT = 0
BROKER_CONNECTION_TIMEOUT = 1

# For the Result Store, use the django cache named 'celery'
CELERY_RESULT_BACKEND = 'djcelery.backends.cache:CacheBackend'

# When the broker is behind an ELB, use a heartbeat to refresh the
# connection and to detect if it has been dropped.
s('BROKER_HEARTBEAT', 60.0)
s('BROKER_HEARTBEAT_CHECKRATE', 2)

# Each worker should only fetch one message at a time
CELERYD_PREFETCH_MULTIPLIER = 1

# Rename the exchange and queues for each variant

QUEUE_VARIANT = CONFIG_PREFIX.lower()

CELERY_DEFAULT_EXCHANGE = 'edx.{0}core'.format(QUEUE_VARIANT)

HIGH_PRIORITY_QUEUE = 'edx.{0}core.high'.format(QUEUE_VARIANT)
DEFAULT_PRIORITY_QUEUE = 'edx.{0}core.default'.format(QUEUE_VARIANT)
HIGH_MEM_QUEUE = 'edx.{0}core.high_mem'.format(QUEUE_VARIANT)

CELERY_DEFAULT_QUEUE = DEFAULT_PRIORITY_QUEUE
CELERY_DEFAULT_ROUTING_KEY = DEFAULT_PRIORITY_QUEUE

CELERY_QUEUES = {
    HIGH_PRIORITY_QUEUE: {},
    DEFAULT_PRIORITY_QUEUE: {},
    HIGH_MEM_QUEUE: {},
}

CELERY_ROUTES = "{}celery.Router".format(QUEUE_VARIANT)
CELERYBEAT_SCHEDULE = {}  # For scheduling tasks, entries can be added to this dict

# STATIC_ROOT specifies the directory where static files are
# collected
s('STATIC_ROOT_BASE')
if STATIC_ROOT_BASE:
    STATIC_ROOT = path(STATIC_ROOT_BASE)
    WEBPACK_LOADER['DEFAULT']['STATS_FILE'] = STATIC_ROOT / "webpack-stats.json"
    WEBPACK_LOADER['WORKERS']['STATS_FILE'] = STATIC_ROOT / "webpack-worker-stats.json"


# STATIC_URL_BASE specifies the base url to use for static files
STATIC_URL_BASE = s('STATIC_URL_BASE')
if STATIC_URL_BASE:
    STATIC_URL = STATIC_URL_BASE
    if not STATIC_URL.endswith("/"):
        STATIC_URL += "/"

# DEFAULT_COURSE_ABOUT_IMAGE_URL specifies the default image to show for courses that don't provide one
s('DEFAULT_COURSE_ABOUT_IMAGE_URL')

# COURSE_MODE_DEFAULTS specifies the course mode to use for courses that do not set one
s('COURSE_MODE_DEFAULTS')

# MEDIA_ROOT specifies the directory where user-uploaded files are stored.
s('MEDIA_ROOT')
s('MEDIA_URL')

# The following variables use (or) instead of the default value inside (get). This is to enforce using the Lazy Text
# values when the varibale is an empty string. Therefore, setting these variable as empty text in related
# json files will make the system reads thier values from django translation files
s('PLATFORM_NAME')
s('PLATFORM_DESCRIPTION')

# For displaying on the receipt. At Stanford PLATFORM_NAME != MERCHANT_NAME, but PLATFORM_NAME is a fine default
s('PLATFORM_TWITTER_ACCOUNT')
s('PLATFORM_FACEBOOK_ACCOUNT')

s('SOCIAL_SHARING_SETTINGS')

# Social media links for the page footer
s('SOCIAL_MEDIA_FOOTER_URLS')

s('CC_MERCHANT_NAME', PLATFORM_NAME)
s('EMAIL_BACKEND')
s('EMAIL_FILE_PATH')
s('EMAIL_HOST', 'localhost')  # django default is localhost
s('EMAIL_PORT', 25)  # django default is 25
s('EMAIL_USE_TLS', False)  # django default is False
s('SITE_NAME')
s('HTTPS')
s('SESSION_ENGINE')
s('SESSION_COOKIE_DOMAIN')
s('SESSION_COOKIE_HTTPONLY', True)
s('SESSION_COOKIE_SECURE')
s('SESSION_SAVE_EVERY_REQUEST')

s('AWS_SES_REGION_NAME', 'us-east-1')
s('AWS_SES_REGION_ENDPOINT', 'email.us-east-1.amazonaws.com')

s('REGISTRATION_EXTRA_FIELDS')
s('REGISTRATION_EXTENSION_FORM')
s('REGISTRATION_EMAIL_PATTERNS_ALLOWED')
s('REGISTRATION_FIELD_ORDER')

# Set the names of cookies shared with the marketing site
# These have the same cookie domain as the session, which in production
# usually includes subdomains.
s('EDXMKTG_LOGGED_IN_COOKIE_NAME')
s('EDXMKTG_USER_INFO_COOKIE_NAME')

s('LMS_ROOT_URL')
s('LMS_INTERNAL_ROOT_URL', LMS_ROOT_URL)

# List of logout URIs for each IDA that the learner should be logged out of when they logout of the LMS. Only applies to
# IDA for which the social auth flow uses DOT (Django OAuth Toolkit).
s('IDA_LOGOUT_URI_LIST', [])

extra_features = s('EXTRA_FEATURES', {}, set_global=False)
for name, value in extra_features.items():
    FEATURES[name] = value

s('CMS_BASE', 'studio.edx.org')

ALLOWED_HOSTS = [
    # TODO: bbeggs remove this before prod, temp fix to get load testing running
    "*",
    s('LMS_BASE', set_global=False),
    FEATURES['PREVIEW_LMS_BASE'],
]

# allow for environments to specify what cookie name our login subsystem should use
# this is to fix a bug regarding simultaneous logins between edx.org and edge.edx.org which can
# happen with some browsers (e.g. Firefox)
s('SESSION_COOKIE_NAME')

s('CACHES')
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
STATICFILES_STORAGE = os.environ.get('STATICFILES_STORAGE', s('STATICFILES_STORAGE', set_global=False))
s('STATICFILES_STORAGE_KWARGS')

# Load all AWS_ prefixed variables to allow an S3Boto3Storage to be configured
_locals = locals()
for key, value in __config__.items():
    if key.startswith('AWS_'):
        _locals[key] = value

# Email overrides
s('DEFAULT_FROM_EMAIL')
s('DEFAULT_FEEDBACK_EMAIL')
s('ADMINS')
s('SERVER_EMAIL')
s('TECH_SUPPORT_EMAIL')
s('CONTACT_EMAIL')
s('BUGS_EMAIL')
s('PAYMENT_SUPPORT_EMAIL')
s('FINANCE_EMAIL')
s('UNIVERSITY_EMAIL')
s('PRESS_EMAIL')

s('CONTACT_MAILING_ADDRESS')

# Account activation email sender address
s('ACTIVATION_EMAIL_FROM_ADDRESS')

# Currency
s('PAID_COURSE_REGISTRATION_CURRENCY')

# Payment Report Settings
s('PAYMENT_REPORT_GENERATOR_GROUP')

# Bulk Email overrides
s('BULK_EMAIL_DEFAULT_FROM_EMAIL')
s('BULK_EMAIL_EMAILS_PER_TASK')
s('BULK_EMAIL_DEFAULT_RETRY_DELAY')
s('BULK_EMAIL_MAX_RETRIES')
s('BULK_EMAIL_INFINITE_RETRY_CAP')
s('BULK_EMAIL_LOG_SENT_EMAILS')
s('BULK_EMAIL_RETRY_DELAY_BETWEEN_SENDS')
# We want Bulk Email running on the high-priority queue, so we define the
# routing key that points to it. At the moment, the name is the same.
# We have to reset the value here, since we have changed the value of the queue name.
s('BULK_EMAIL_ROUTING_KEY', HIGH_PRIORITY_QUEUE)

# We can run smaller jobs on the low priority queue. See note above for why
# we have to reset the value here.
s('BULK_EMAIL_ROUTING_KEY_SMALL_JOBS', DEFAULT_PRIORITY_QUEUE)

# Queue to use for expiring old entitlements
s('ENTITLEMENTS_EXPIRATION_ROUTING_KEY', DEFAULT_PRIORITY_QUEUE)

# Message expiry time in seconds
s('CELERY_EVENT_QUEUE_TTL')

# Allow CELERY_QUEUES to be overwritten by __config__
s('CELERY_QUEUES')

# Then add alternate environment queues
ALTERNATE_QUEUE_ENVS = s('ALTERNATE_WORKER_QUEUES', '').split()
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

# following setting is for backward compatibility
s('COMPREHENSIVE_THEME_DIR')

s('COMPREHENSIVE_THEME_DIRS', [])

# COMPREHENSIVE_THEME_LOCALE_PATHS contain the paths to themes locale directories e.g.
# 'COMPREHENSIVE_THEME_LOCALE_PATHS' : [
#        '/edx/src/edx-themes/conf/locale'
#    ],
s('COMPREHENSIVE_THEME_LOCALE_PATHS', [])

s('DEFAULT_SITE_THEME')
s('ENABLE_COMPREHENSIVE_THEMING')

MKTG_URL_LINK_MAP.update(__config__.get('EXTRA_MKTG_URL_LINK_MAP', {}))
s('ENTERPRISE_MARKETING_FOOTER_QUERY_PARAMS')
# Marketing link overrides
MKTG_URL_OVERRIDES.update(__config__.get('EXTRA_MKTG_URL_OVERRIDES', MKTG_URL_OVERRIDES))

# Intentional defaults.
s('SUPPORT_SITE_LINK')
s('ID_VERIFICATION_SUPPORT_LINK', SUPPORT_SITE_LINK)
s('PASSWORD_RESET_SUPPORT_LINK', SUPPORT_SITE_LINK)
s('ACTIVATION_EMAIL_SUPPORT_LINK', SUPPORT_SITE_LINK)

# Mobile store URL overrides
MOBILE_STORE_URLS = s('MOBILE_STORE_URLS')

# Timezone overrides
TIME_ZONE = s('CELERY_TIMEZONE')

# Translation overrides
LANGUAGES = s('LANGUAGES')
s('CERTIFICATE_TEMPLATE_LANGUAGES')
LANGUAGE_DICT = dict(LANGUAGES)
s('LANGUAGE_CODE')
s('LANGUAGE_COOKIE')
s('ALL_LANGUAGES')

s('USE_I18N')

# Additional installed apps
for app in __config__.get('ADDL_INSTALLED_APPS', []):
    INSTALLED_APPS.append(app)

s('WIKI_ENABLED')

s('DATA_DIR', DATA_DIR)

LOGGING = get_logger_config(s('LOG_DIR', set_global=False),
                            logging_env=s('LOGGING_ENV', set_global=False),
                            local_loglevel=s('LOCAL_LOGLEVEL', default='INFO', set_global=False),
                            service_variant=SERVICE_VARIANT)

s('COURSE_LISTINGS', {})
s('COMMENTS_SERVICE_URL', '')
s('COMMENTS_SERVICE_KEY', '')
s('CERT_NAME_SHORT')
s('CERT_NAME_LONG')
s('CERT_QUEUE', 'test-pull')
s('ZENDESK_URL')
s('ZENDESK_CUSTOM_FIELDS')
s('ZENDESK_GROUP_ID_MAPPING')

s('MKTG_URLS')

# Badgr API
s('BADGR_API_TOKEN')
s('BADGR_BASE_URL')
s('BADGR_ISSUER_SLUG')
s('BADGR_TIMEOUT')

# git repo loading  environment
s('GIT_REPO_DIR', '/edx/var/edxapp/course_repos')
s('GIT_IMPORT_STATIC', True)
s('GIT_IMPORT_PYTHON_LIB', True)
s('PYTHON_LIB_FILENAME', 'python_lib.zip')

for name, value in s('CODE_JAIL', {}).items():
    oldvalue = CODE_JAIL.get(name)
    if isinstance(oldvalue, dict):
        for subname, subvalue in value.items():
            oldvalue[subname] = subvalue
    else:
        CODE_JAIL[name] = value

s('COURSES_WITH_UNSAFE_CODE', [])

s('ASSET_IGNORE_REGEX')

# Event Tracking
s('TRACKING_IGNORE_URL_PATTERNS')

# SSL external authentication settings
s('SSL_AUTH_EMAIL_DOMAIN', 'MIT.EDU')
s(
    'SSL_AUTH_DN_FORMAT_STRING',
    u'/C=US/ST=Massachusetts/O=Massachusetts Institute of Technology/OU=Client CA v1/CN={0}/emailAddress={1}'
)

# Video Caching. Pairing country codes with CDN URLs.
# Example: {'CN': 'http://api.xuetangx.com/edx/video?s3_url='}
s('VIDEO_CDN_URL', {})

# Branded footer
s('FOOTER_OPENEDX_URL')
s('FOOTER_OPENEDX_LOGO_IMAGE')
s('FOOTER_ORGANIZATION_IMAGE')
s('FOOTER_CACHE_TIMEOUT')
s('FOOTER_BROWSER_CACHE_MAX_AGE')

# Credit notifications settings
s('NOTIFICATION_EMAIL_CSS')
s('NOTIFICATION_EMAIL_EDX_LOGO')

# Determines whether the CSRF token can be transported on
# unencrypted channels. It is set to False here for backward compatibility,
# but it is highly recommended that this is True for enviroments accessed
# by end users.
s('CSRF_COOKIE_SECURE', False)

# Determines which origins are trusted for unsafe requests eg. POST requests.
s('CSRF_TRUSTED_ORIGINS', [])

# Whitelist of domains to which the login/logout pages will redirect.
s('LOGIN_REDIRECT_WHITELIST')

############# CORS headers for cross-domain requests #################

if FEATURES.get('ENABLE_CORS_HEADERS') or FEATURES.get('ENABLE_CROSS_DOMAIN_CSRF_COOKIE'):
    CORS_ALLOW_CREDENTIALS = True
    s('CORS_ORIGIN_WHITELIST', ())
    s('CORS_ORIGIN_ALLOW_ALL', False)
    s('CORS_ALLOW_INSECURE', False)
    CORS_ALLOW_HEADERS = corsheaders_default_headers + (
        'use-jwt-cookie',
    )

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
    s('CROSS_DOMAIN_CSRF_COOKIE_NAME')

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
    s('CROSS_DOMAIN_CSRF_COOKIE_DOMAIN')


# Field overrides. To use the IDDE feature, add
# 'courseware.student_field_overrides.IndividualStudentOverrideProvider'.
s('FIELD_OVERRIDE_PROVIDERS', [])

############### XBlock filesystem field config ##########
s('DJFS')

############### Module Store Items ##########
s('HOSTNAME_MODULESTORE_DEFAULT_MAPPINGS', {})
# PREVIEW DOMAIN must be present in HOSTNAME_MODULESTORE_DEFAULT_MAPPINGS for the preview to show draft changes
if 'PREVIEW_LMS_BASE' in FEATURES and FEATURES['PREVIEW_LMS_BASE'] != '':
    PREVIEW_DOMAIN = FEATURES['PREVIEW_LMS_BASE'].split(':')[0]
    # update dictionary with preview domain regex
    HOSTNAME_MODULESTORE_DEFAULT_MAPPINGS.update({
        PREVIEW_DOMAIN: 'draft-preferred'
    })

s('MODULESTORE_FIELD_OVERRIDE_PROVIDERS')

s('XBLOCK_FIELD_DATA_WRAPPERS')

############### Mixed Related(Secure/Not-Secure) Items ##########
LMS_SEGMENT_KEY = s('SEGMENT_KEY', set_global=False)

s('CC_PROCESSOR_NAME')
s('CC_PROCESSOR')

s('SECRET_KEY')

s('AWS_ACCESS_KEY_ID')

s('AWS_SECRET_ACCESS_KEY')

s('AWS_STORAGE_BUCKET_NAME', 'edxuploads')

# Disabling querystring auth instructs Boto to exclude the querystring parameters (e.g. signature, access key) it
# normally appends to every returned URL.
s('AWS_QUERYSTRING_AUTH', True)
s('AWS_S3_CUSTOM_DOMAIN', 'edxuploads.s3.amazonaws.com')

if __config__.get('DEFAULT_FILE_STORAGE'):
    s('DEFAULT_FILE_STORAGE')
elif AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
else:
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Specific setting for the File Upload Service to store media in a bucket.
s('FILE_UPLOAD_STORAGE_BUCKET_NAME')
s('FILE_UPLOAD_STORAGE_PREFIX')

# If there is a database called 'read_replica', you can use the use_read_replica_if_available
# function in util/query.py, which is useful for very large database reads
s('DATABASES')

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

s('XQUEUE_INTERFACE')

# Get the MODULESTORE from auth.json, but if it doesn't exist,
# use the one from common.py
MODULESTORE = convert_module_store_setting_if_needed(s('MODULESTORE', set_global=False))
s('CONTENTSTORE')
s('DOC_STORE_CONFIG')
s('MONGODB_LOG', {})

s('EMAIL_HOST_USER', '')  # django default is ''
s('EMAIL_HOST_PASSWORD', '')  # django default is ''

############################### BLOCKSTORE #####################################
s('BLOCKSTORE_API_URL')  # e.g. 'https://blockstore.example.com/api/v1/'
# Configure an API auth token at (blockstore URL)/admin/authtoken/token/
s('BLOCKSTORE_API_AUTH_TOKEN')

# Datadog for events!
s('DATADOG', {})

# TODO: deprecated (compatibility with previous settings)
if 'DATADOG_API' in __config__:
    DATADOG['api_key'] = __config__['DATADOG_API']

# Analytics API
s('ANALYTICS_API_KEY')
s('ANALYTICS_API_URL')

# Zendesk
s('ZENDESK_USER')
s('ZENDESK_API_KEY')

# API Key for inbound requests from Notifier service
s('EDX_API_KEY')

# Celery Broker
s('CELERY_BROKER_TRANSPORT', '')
s('CELERY_BROKER_HOSTNAME', '')
s('CELERY_BROKER_VHOST', '')
s('CELERY_BROKER_USER', '')
s('CELERY_BROKER_PASSWORD', '')

BROKER_URL = '{0}://{1}:{2}@{3}/{4}'.format(CELERY_BROKER_TRANSPORT,
                                            CELERY_BROKER_USER,
                                            CELERY_BROKER_PASSWORD,
                                            CELERY_BROKER_HOSTNAME,
                                            CELERY_BROKER_VHOST)
BROKER_USE_SSL = s('CELERY_BROKER_USE_SSL', False)

# Block Structures
s('BLOCK_STRUCTURES_SETTINGS')

# upload limits
s('STUDENT_FILEUPLOAD_MAX_SIZE')

# Event tracking
TRACKING_BACKENDS.update(s('EXTRA_TRACKING_BACKENDS', {}, set_global=False))
EVENT_TRACKING_BACKENDS['tracking_logs']['OPTIONS']['backends'].update(
    s('EXTRA_EVENT_TRACKING_BACKENDS', {}, set_global=False)
)
EVENT_TRACKING_BACKENDS['segmentio']['OPTIONS']['processors'][0]['OPTIONS']['whitelist'].extend(
    s('EVENT_TRACKING_SEGMENTIO_EMIT_WHITELIST', [], set_global=False))
s('TRACKING_SEGMENTIO_WEBHOOK_SECRET')
s('TRACKING_SEGMENTIO_ALLOWED_TYPES')
s('TRACKING_SEGMENTIO_DISALLOWED_SUBSTRING_NAMES')
s('TRACKING_SEGMENTIO_SOURCE_MAP')

# Heartbeat
s('HEARTBEAT_CHECKS')
s('HEARTBEAT_EXTENDED_CHECKS')
s('HEARTBEAT_CELERY_TIMEOUT')

# Student identity verification settings
s('VERIFY_STUDENT')
s('DISABLE_ACCOUNT_ACTIVATION_REQUIREMENT_SWITCH')

# Grades download
s('GRADES_DOWNLOAD_ROUTING_KEY', HIGH_MEM_QUEUE)

s('GRADES_DOWNLOAD')

# Rate limit for regrading tasks that a grading policy change can kick off
s('POLICY_CHANGE_TASK_RATE_LIMIT')

# financial reports
s('FINANCIAL_REPORTS')

##### ORA2 ######
# Prefix for uploads of example-based assessment AI classifiers
# This can be used to separate uploads for different environments
# within the same S3 bucket.
s('ORA2_FILE_PREFIX')

##### ACCOUNT LOCKOUT DEFAULT PARAMETERS #####
s('MAX_FAILED_LOGIN_ATTEMPTS_ALLOWED')

s('MAX_FAILED_LOGIN_ATTEMPTS_LOCKOUT_PERIOD_SECS')

#### PASSWORD POLICY SETTINGS #####
s('AUTH_PASSWORD_VALIDATORS')

### INACTIVITY SETTINGS ####
s('SESSION_INACTIVITY_TIMEOUT_IN_SECONDS', )

##### LMS DEADLINE DISPLAY TIME_ZONE #######
s('TIME_ZONE_DISPLAYED_FOR_DEADLINES')

##### X-Frame-Options response header settings #####
s('X_FRAME_OPTIONS')

##### Third-party auth options ################################################
if FEATURES.get('ENABLE_THIRD_PARTY_AUTH'):
    third_party_auth_backends = s('THIRD_PARTY_AUTH_BACKENDS', [
        'social_core.backends.google.GoogleOAuth2',
        'social_core.backends.linkedin.LinkedinOAuth2',
        'social_core.backends.facebook.FacebookOAuth2',
        'social_core.backends.azuread.AzureADOAuth2',
        'third_party_auth.identityserver3.IdentityServer3',
        'third_party_auth.saml.SAMLAuthBackend',
        'third_party_auth.lti.LTIAuthBackend',
    ], set_global=False)

    AUTHENTICATION_BACKENDS = list(third_party_auth_backends) + list(AUTHENTICATION_BACKENDS)
    print("auth backends: %s" % str(AUTHENTICATION_BACKENDS))
    del third_party_auth_backends

    # The reduced session expiry time during the third party login pipeline. (Value in seconds)
    s('SOCIAL_AUTH_PIPELINE_TIMEOUT', 600)

    # Most provider configuration is done via ConfigurationModels but for a few sensitive values
    # we allow configuration via conf file instead (optionally).
    # The SAML private/public key values do not need the delimiter lines (such as
    # "-----BEGIN PRIVATE KEY-----", "-----END PRIVATE KEY-----" etc.) but they may be included
    # if you want (though it's easier to format the key values as JSON without the delimiters).
    s('SOCIAL_AUTH_SAML_SP_PRIVATE_KEY', '')
    s('SOCIAL_AUTH_SAML_SP_PUBLIC_CERT', '')
    s('SOCIAL_AUTH_SAML_SP_PRIVATE_KEY_DICT', {})
    s('SOCIAL_AUTH_SAML_SP_PUBLIC_CERT_DICT', {})
    s('SOCIAL_AUTH_OAUTH_SECRETS', {})
    s('SOCIAL_AUTH_LTI_CONSUMER_SECRETS', {})

    # third_party_auth config moved to ConfigurationModels. This is for data migration only:
    THIRD_PARTY_AUTH_OLD_CONFIG = s('THIRD_PARTY_AUTH', set_global=False)

    period_hours = s('THIRD_PARTY_AUTH_SAML_FETCH_PERIOD_HOURS', 24, set_global=False)
    if period_hours is not None:
        CELERYBEAT_SCHEDULE['refresh-saml-metadata'] = {
            'task': 'third_party_auth.fetch_saml_metadata',
            'schedule': datetime.timedelta(hours=period_hours),
        }
    del period_hours

    # The following can be used to integrate a custom login form with third_party_auth.
    # It should be a dict where the key is a word passed via ?auth_entry=, and the value is a
    # dict with an arbitrary 'secret_key' and a 'url'.
    s('THIRD_PARTY_AUTH_CUSTOM_AUTH_FORMS', {})

##### OAUTH2 Provider ##############
if FEATURES.get('ENABLE_OAUTH2_PROVIDER'):
    s('OAUTH_ENFORCE_SECURE', True)
    s('OAUTH_ENFORCE_CLIENT_SECURE', True)
    # Defaults for the following are defined in lms.envs.common
    OAUTH_EXPIRE_DELTA = datetime.timedelta(
        days=s('OAUTH_EXPIRE_CONFIDENTIAL_CLIENT_DAYS')
    )
    OAUTH_EXPIRE_DELTA_PUBLIC = datetime.timedelta(
        days=s('OAUTH_EXPIRE_PUBLIC_CLIENT_DAYS')
    )
    s('OAUTH_ID_TOKEN_EXPIRATION')
    s('OAUTH_DELETE_EXPIRED')


##### GOOGLE ANALYTICS IDS #####
s('GOOGLE_ANALYTICS_ACCOUNT')
s('GOOGLE_ANALYTICS_TRACKING_ID')
s('GOOGLE_ANALYTICS_LINKEDIN')
s('GOOGLE_SITE_VERIFICATION_ID')

##### BRANCH.IO KEY #####
s('BRANCH_IO_KEY')

##### OPTIMIZELY PROJECT ID #####
s('OPTIMIZELY_PROJECT_ID')

#### Course Registration Code length ####
s('REGISTRATION_CODE_LENGTH', 8)

# REGISTRATION CODES DISPLAY INFORMATION
s('INVOICE_CORP_ADDRESS')
s('INVOICE_PAYMENT_INSTRUCTIONS')

# Which access.py permission names to check;
# We default this to the legacy permission 'see_exists'.
s('COURSE_CATALOG_VISIBILITY_PERMISSION')
s('COURSE_ABOUT_VISIBILITY_PERMISSION')
s('DEFAULT_COURSE_VISIBILITY_IN_CATALOG')
s('DEFAULT_MOBILE_AVAILABLE')


# Enrollment API Cache Timeout
s('ENROLLMENT_COURSE_DETAILS_CACHE_TIMEOUT', 60)

# PDF RECEIPT/INVOICE OVERRIDES
s('PDF_RECEIPT_TAX_ID')
s('PDF_RECEIPT_FOOTER_TEXT')
s('PDF_RECEIPT_DISCLAIMER_TEXT')
s('PDF_RECEIPT_BILLING_ADDRESS')
s('PDF_RECEIPT_TERMS_AND_CONDITIONS')
s('PDF_RECEIPT_TAX_ID_LABEL')
s('PDF_RECEIPT_LOGO_PATH')
s('PDF_RECEIPT_COBRAND_LOGO_PATH')
s('PDF_RECEIPT_LOGO_HEIGHT_MM')
s('PDF_RECEIPT_COBRAND_LOGO_HEIGHT_MM')

if FEATURES.get('ENABLE_COURSEWARE_SEARCH') or \
   FEATURES.get('ENABLE_DASHBOARD_SEARCH') or \
   FEATURES.get('ENABLE_COURSE_DISCOVERY') or \
   FEATURES.get('ENABLE_TEAMS'):
    # Use ElasticSearch as the search engine herein
    SEARCH_ENGINE = 'search.elastic.ElasticSearchEngine'

s('ELASTIC_SEARCH_CONFIG', [{}])

# Facebook app
s('FACEBOOK_API_VERSION')
s('FACEBOOK_APP_SECRET')
s('FACEBOOK_APP_ID')

s('XBLOCK_SETTINGS', {})
XBLOCK_SETTINGS.setdefault('VideoBlock', {})['licensing_enabled'] = FEATURES.get('LICENSING', False)
XBLOCK_SETTINGS.setdefault('VideoBlock', {})['YOUTUBE_API_KEY'] = s('YOUTUBE_API_KEY')

##### VIDEO IMAGE STORAGE #####
s('VIDEO_IMAGE_SETTINGS')

##### VIDEO TRANSCRIPTS STORAGE #####
s('VIDEO_TRANSCRIPTS_SETTINGS')

##### ECOMMERCE API CONFIGURATION SETTINGS #####
s('ECOMMERCE_PUBLIC_URL_ROOT')
s('ECOMMERCE_API_URL')
s('ECOMMERCE_API_TIMEOUT')

s('COURSE_CATALOG_API_URL')

s('ECOMMERCE_SERVICE_WORKER_USERNAME')

##### Custom Courses for EdX #####
if FEATURES.get('CUSTOM_COURSES_EDX'):
    INSTALLED_APPS += ['lms.djangoapps.ccx', 'openedx.core.djangoapps.ccxcon.apps.CCXConnectorConfig']
    MODULESTORE_FIELD_OVERRIDE_PROVIDERS += (
        'lms.djangoapps.ccx.overrides.CustomCoursesForEdxOverrideProvider',
    )
s('CCX_MAX_STUDENTS_ALLOWED')

##### Individual Due Date Extensions #####
if FEATURES.get('INDIVIDUAL_DUE_DATES'):
    FIELD_OVERRIDE_PROVIDERS += (
        'courseware.student_field_overrides.IndividualStudentOverrideProvider',
    )

##### Self-Paced Course Due Dates #####
XBLOCK_FIELD_DATA_WRAPPERS += (
    'lms.djangoapps.courseware.field_overrides:OverrideModulestoreFieldData.wrap',
)

MODULESTORE_FIELD_OVERRIDE_PROVIDERS += (
    'lms.djangoapps.courseware.self_paced_overrides.SelfPacedDateOverrideProvider',
)

# PROFILE IMAGE CONFIG
s('PROFILE_IMAGE_BACKEND')
s('PROFILE_IMAGE_HASH_SEED')
s('PROFILE_IMAGE_MAX_BYTES')
s('PROFILE_IMAGE_MIN_BYTES')
PROFILE_IMAGE_DEFAULT_FILENAME = 'images/profiles/default'
s('PROFILE_IMAGE_SIZES_MAP')

# EdxNotes config

s('EDXNOTES_PUBLIC_API')
s('EDXNOTES_INTERNAL_API')
s('EDXNOTES_CLIENT_NAME')

s('EDXNOTES_CONNECT_TIMEOUT')
s('EDXNOTES_READ_TIMEOUT')

##### Credit Provider Integration #####

s('CREDIT_PROVIDER_SECRET_KEYS', {})

##################### LTI Provider #####################
if FEATURES.get('ENABLE_LTI_PROVIDER'):
    INSTALLED_APPS.append('lti_provider.apps.LtiProviderConfig')
    AUTHENTICATION_BACKENDS.append('lti_provider.users.LtiBackend')

s('LTI_USER_EMAIL_DOMAIN', 'lti.example.com')

# For more info on this, see the notes in common.py
s('LTI_AGGREGATE_SCORE_PASSBACK_DELAY')

##################### Credit Provider help link ####################
s('CREDIT_HELP_LINK_URL')

#### JWT configuration ####
JWT_AUTH.update(s('EXTRA_JWT_AUTH', {}, set_global=False))

# Offset for pk of courseware.StudentModuleHistoryExtended
s('STUDENTMODULEHISTORYEXTENDED_OFFSET')

# Cutoff date for granting audit certificates
audit_cert_cutoff_date = s('AUDIT_CERT_CUTOFF_DATE', set_global=False)
if audit_cert_cutoff_date:
    AUDIT_CERT_CUTOFF_DATE = dateutil.parser.parse(audit_cert_cutoff_date)
del audit_cert_cutoff_date

################################ Settings for Credentials Service ################################

s('CREDENTIALS_GENERATION_ROUTING_KEY', DEFAULT_PRIORITY_QUEUE)

# Queue to use for award program certificates
s('PROGRAM_CERTIFICATES_ROUTING_KEY', DEFAULT_PRIORITY_QUEUE)

s('API_ACCESS_MANAGER_EMAIL')
s('API_ACCESS_FROM_EMAIL')

# Mobile App Version Upgrade config
s('APP_UPGRADE_CACHE_TIMEOUT')

s('AFFILIATE_COOKIE_NAME')

############## Settings for LMS Context Sensitive Help ##############

s('HELP_TOKENS_BOOKS')


############## OPEN EDX ENTERPRISE SERVICE CONFIGURATION ######################
# The Open edX Enterprise service is currently hosted via the LMS container/process.
# However, for all intents and purposes this service is treated as a standalone IDA.
# These configuration settings are specific to the Enterprise service and you should
# not find references to them within the edx-platform project.

# Publicly-accessible enrollment URL, for use on the client side.
s(
    'ENTERPRISE_PUBLIC_ENROLLMENT_API_URL',
    (LMS_ROOT_URL or '') + LMS_ENROLLMENT_API_PATH
)

# Enrollment URL used on the server-side.
s(
    'ENTERPRISE_ENROLLMENT_API_URL',
    (LMS_INTERNAL_ROOT_URL or '') + LMS_ENROLLMENT_API_PATH
)

# Enterprise logo image size limit in KB's
s('ENTERPRISE_CUSTOMER_LOGO_IMAGE_SIZE')

# Course enrollment modes to be hidden in the Enterprise enrollment page
# if the 'Hide audit track' flag is enabled for an EnterpriseCustomer
s('ENTERPRISE_COURSE_ENROLLMENT_AUDIT_MODES')

# A support URL used on Enterprise landing pages for when a warning
# message goes off.
s('ENTERPRISE_SUPPORT_URL')

# A default dictionary to be used for filtering out enterprise customer catalog.
s('ENTERPRISE_CUSTOMER_CATALOG_DEFAULT_CONTENT_FILTER')

############## ENTERPRISE SERVICE API CLIENT CONFIGURATION ######################
# The LMS communicates with the Enterprise service via the EdxRestApiClient class
# The below environmental settings are utilized by the LMS when interacting with
# the service, and override the default parameters which are defined in common.py

DEFAULT_ENTERPRISE_API_URL = None
if LMS_INTERNAL_ROOT_URL is not None:
    DEFAULT_ENTERPRISE_API_URL = LMS_INTERNAL_ROOT_URL + '/enterprise/api/v1/'
s('ENTERPRISE_API_URL', DEFAULT_ENTERPRISE_API_URL)

DEFAULT_ENTERPRISE_CONSENT_API_URL = None
if LMS_INTERNAL_ROOT_URL is not None:
    DEFAULT_ENTERPRISE_CONSENT_API_URL = LMS_INTERNAL_ROOT_URL + '/consent/api/v1/'
s('ENTERPRISE_CONSENT_API_URL', DEFAULT_ENTERPRISE_CONSENT_API_URL)

s('ENTERPRISE_SERVICE_WORKER_USERNAME')
s('ENTERPRISE_API_CACHE_TIMEOUT')
s('ENTERPRISE_CATALOG_INTERNAL_ROOT_URL')


############## ENTERPRISE SERVICE LMS CONFIGURATION ##################################
# The LMS has some features embedded that are related to the Enterprise service, but
# which are not provided by the Enterprise service. These settings override the
# base values for the parameters as defined in common.py

s('ENTERPRISE_PLATFORM_WELCOME_TEMPLATE')
s('ENTERPRISE_SPECIFIC_BRANDED_WELCOME_TEMPLATE')
s('ENTERPRISE_TAGLINE')
s('ENTERPRISE_EXCLUDED_REGISTRATION_FIELDS')
s('BASE_COOKIE_DOMAIN')
s('SYSTEM_TO_FEATURE_ROLE_MAPPING')

############## CATALOG/DISCOVERY SERVICE API CLIENT CONFIGURATION ######################
# The LMS communicates with the Catalog service via the EdxRestApiClient class
# The below environmental settings are utilized by the LMS when interacting with
# the service, and override the default parameters which are defined in common.py

s('COURSES_API_CACHE_TIMEOUT')

# Add an ICP license for serving content in China if your organization is registered to do so
s('ICP_LICENSE')
s('ICP_LICENSE_INFO', {})

############## Settings for CourseGraph ############################
s('COURSEGRAPH_JOB_QUEUE', DEFAULT_PRIORITY_QUEUE)

# How long to cache OpenAPI schemas and UI, in seconds.
s('OPENAPI_CACHE_TIMEOUT', 60 * 60)

########################## Parental controls config  #######################

# The age at which a learner no longer requires parental consent, or None
# if parental consent is never required.
s('PARENTAL_CONSENT_AGE_LIMIT')

########################## Extra middleware classes  #######################

# Allow extra middleware classes to be added to the app through configuration.
MIDDLEWARE.extend(s('EXTRA_MIDDLEWARE_CLASSES', []))

########################## Settings for Completion API #####################

# Once a user has watched this percentage of a video, mark it as complete:
# (0.0 = 0%, 1.0 = 100%)
s('COMPLETION_VIDEO_COMPLETE_PERCENTAGE')
# The time a block needs to be viewed to be considered complete, in milliseconds.
s('COMPLETION_BY_VIEWING_DELAY_MS')

############### Settings for django-fernet-fields ##################
s('FERNET_KEYS')

################# Settings for the maintenance banner #################
s('MAINTENANCE_BANNER_TEXT')

############### Settings for Retirement #####################
s('RETIRED_USERNAME_PREFIX')
s('RETIRED_EMAIL_PREFIX')
s('RETIRED_EMAIL_DOMAIN')
s('RETIRED_USER_SALTS')
s('RETIREMENT_SERVICE_WORKER_USERNAME')
s('RETIREMENT_STATES')

############### Settings for Username Replacement ###############

s('USERNAME_REPLACEMENT_WORKER')

############## Settings for Course Enrollment Modes ######################
s('COURSE_ENROLLMENT_MODES')

############## Settings for Microfrontend URLS  #########################
s('WRITABLE_GRADEBOOK_URL')
s('PROFILE_MICROFRONTEND_URL')
s('ORDER_HISTORY_MICROFRONTEND_URL')
s('ACCOUNT_MICROFRONTEND_URL')
s('LEARNING_MICROFRONTEND_URL')
s('LEARNER_PORTAL_URL_ROOT')

############### Settings for edx-rbac  ###############
s('SYSTEM_WIDE_ROLE_CLASSES')

############################### Plugin Settings ###############################

# This is at the bottom because it is going to load more settings after base settings are loaded

# Load production.py in plugins
plugin_settings.add_plugins(__name__, plugin_constants.ProjectType.LMS, plugin_constants.SettingsType.PRODUCTION)

########################## Derive Any Derived Settings  #######################

derive_settings(__name__)

######################### Overriding custom enrollment roles ###############

s('MANUAL_ENROLLMENT_ROLE_CHOICES')

########################## limiting dashboard courses ######################

s('DASHBOARD_COURSE_LIMIT')
