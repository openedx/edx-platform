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

import datetime
import json
import os
import logging
import dateutil

from corsheaders.defaults import default_headers as corsheaders_default_headers
from path import Path as path
from xmodule.modulestore.modulestore_settings import convert_module_store_setting_if_needed

from .common import *

from openedx.core.lib.derived import derive_settings  # pylint: disable=wrong-import-order
from openedx.core.lib.logsettings import get_logger_config  # pylint: disable=wrong-import-order

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

########################## NON-SECURE ENV CONFIG ##############################
# Things like server locations, ports, etc.

with open(CONFIG_ROOT / CONFIG_PREFIX + "env.json") as env_file:
    ENV_TOKENS = json.load(env_file)

# STATIC_ROOT specifies the directory where static files are
# collected
STATIC_ROOT_BASE = ENV_TOKENS.get('STATIC_ROOT_BASE', None)
if STATIC_ROOT_BASE:
    STATIC_ROOT = path(STATIC_ROOT_BASE)
    WEBPACK_LOADER['DEFAULT']['STATS_FILE'] = STATIC_ROOT / "webpack-stats.json"


# STATIC_URL_BASE specifies the base url to use for static files
STATIC_URL_BASE = ENV_TOKENS.get('STATIC_URL_BASE', None)
if STATIC_URL_BASE:
    # collectstatic will fail if STATIC_URL is a unicode string
    STATIC_URL = STATIC_URL_BASE.encode('ascii')
    if not STATIC_URL.endswith("/"):
        STATIC_URL += "/"

# DEFAULT_COURSE_ABOUT_IMAGE_URL specifies the default image to show for courses that don't provide one
DEFAULT_COURSE_ABOUT_IMAGE_URL = ENV_TOKENS.get('DEFAULT_COURSE_ABOUT_IMAGE_URL', DEFAULT_COURSE_ABOUT_IMAGE_URL)

# COURSE_MODE_DEFAULTS specifies the course mode to use for courses that do not set one
COURSE_MODE_DEFAULTS = ENV_TOKENS.get('COURSE_MODE_DEFAULTS', COURSE_MODE_DEFAULTS)

# MEDIA_ROOT specifies the directory where user-uploaded files are stored.
MEDIA_ROOT = ENV_TOKENS.get('MEDIA_ROOT', MEDIA_ROOT)
MEDIA_URL = ENV_TOKENS.get('MEDIA_URL', MEDIA_URL)

PLATFORM_NAME = ENV_TOKENS.get('PLATFORM_NAME', PLATFORM_NAME)
PLATFORM_DESCRIPTION = ENV_TOKENS.get('PLATFORM_DESCRIPTION', PLATFORM_DESCRIPTION)
# For displaying on the receipt. At Stanford PLATFORM_NAME != MERCHANT_NAME, but PLATFORM_NAME is a fine default
PLATFORM_TWITTER_ACCOUNT = ENV_TOKENS.get('PLATFORM_TWITTER_ACCOUNT', PLATFORM_TWITTER_ACCOUNT)
PLATFORM_FACEBOOK_ACCOUNT = ENV_TOKENS.get('PLATFORM_FACEBOOK_ACCOUNT', PLATFORM_FACEBOOK_ACCOUNT)

SOCIAL_SHARING_SETTINGS = ENV_TOKENS.get('SOCIAL_SHARING_SETTINGS', SOCIAL_SHARING_SETTINGS)

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
SESSION_COOKIE_SECURE = ENV_TOKENS.get('SESSION_COOKIE_SECURE', SESSION_COOKIE_SECURE)
SESSION_SAVE_EVERY_REQUEST = ENV_TOKENS.get('SESSION_SAVE_EVERY_REQUEST', SESSION_SAVE_EVERY_REQUEST)

AWS_SES_REGION_NAME = ENV_TOKENS.get('AWS_SES_REGION_NAME', 'us-east-1')
AWS_SES_REGION_ENDPOINT = ENV_TOKENS.get('AWS_SES_REGION_ENDPOINT', 'email.us-east-1.amazonaws.com')

REGISTRATION_EXTRA_FIELDS = ENV_TOKENS.get('REGISTRATION_EXTRA_FIELDS', REGISTRATION_EXTRA_FIELDS)
REGISTRATION_EXTENSION_FORM = ENV_TOKENS.get('REGISTRATION_EXTENSION_FORM', REGISTRATION_EXTENSION_FORM)
REGISTRATION_EMAIL_PATTERNS_ALLOWED = ENV_TOKENS.get('REGISTRATION_EMAIL_PATTERNS_ALLOWED')
REGISTRATION_FIELD_ORDER = ENV_TOKENS.get('REGISTRATION_FIELD_ORDER', REGISTRATION_FIELD_ORDER)

# Set the names of cookies shared with the marketing site
# These have the same cookie domain as the session, which in production
# usually includes subdomains.
EDXMKTG_LOGGED_IN_COOKIE_NAME = ENV_TOKENS.get('EDXMKTG_LOGGED_IN_COOKIE_NAME', EDXMKTG_LOGGED_IN_COOKIE_NAME)
EDXMKTG_USER_INFO_COOKIE_NAME = ENV_TOKENS.get('EDXMKTG_USER_INFO_COOKIE_NAME', EDXMKTG_USER_INFO_COOKIE_NAME)

LMS_ROOT_URL = ENV_TOKENS.get('LMS_ROOT_URL')
LMS_INTERNAL_ROOT_URL = ENV_TOKENS.get('LMS_INTERNAL_ROOT_URL', LMS_ROOT_URL)

# List of logout URIs for each IDA that the learner should be logged out of when they logout of the LMS. Only applies to
# IDA for which the social auth flow uses DOT (Django OAuth Toolkit).
IDA_LOGOUT_URI_LIST = ENV_TOKENS.get('IDA_LOGOUT_URI_LIST', [])

ENV_FEATURES = ENV_TOKENS.get('FEATURES', {})
for feature, value in ENV_FEATURES.items():
    FEATURES[feature] = value

CMS_BASE = ENV_TOKENS.get('CMS_BASE', 'studio.edx.org')

ALLOWED_HOSTS = [
    # TODO: bbeggs remove this before prod, temp fix to get load testing running
    "*",
    ENV_TOKENS.get('LMS_BASE'),
    FEATURES['PREVIEW_LMS_BASE'],
]

# allow for environments to specify what cookie name our login subsystem should use
# this is to fix a bug regarding simultaneous logins between edx.org and edge.edx.org which can
# happen with some browsers (e.g. Firefox)
if ENV_TOKENS.get('SESSION_COOKIE_NAME', None):
    # NOTE, there's a bug in Django (http://bugs.python.org/issue18012) which necessitates this being a str()
    SESSION_COOKIE_NAME = str(ENV_TOKENS.get('SESSION_COOKIE_NAME'))

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

CONTACT_MAILING_ADDRESS = ENV_TOKENS.get('CONTACT_MAILING_ADDRESS', CONTACT_MAILING_ADDRESS)

# Account activation email sender address
ACTIVATION_EMAIL_FROM_ADDRESS = ENV_TOKENS.get('ACTIVATION_EMAIL_FROM_ADDRESS', ACTIVATION_EMAIL_FROM_ADDRESS)

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
BULK_EMAIL_RETRY_DELAY_BETWEEN_SENDS = ENV_TOKENS.get(
    'BULK_EMAIL_RETRY_DELAY_BETWEEN_SENDS',
    BULK_EMAIL_RETRY_DELAY_BETWEEN_SENDS
)
# We want Bulk Email running on the high-priority queue, so we define the
# routing key that points to it. At the moment, the name is the same.
# We have to reset the value here, since we have changed the value of the queue name.
BULK_EMAIL_ROUTING_KEY = ENV_TOKENS.get('BULK_EMAIL_ROUTING_KEY', HIGH_PRIORITY_QUEUE)

# We can run smaller jobs on the low priority queue. See note above for why
# we have to reset the value here.
BULK_EMAIL_ROUTING_KEY_SMALL_JOBS = ENV_TOKENS.get('BULK_EMAIL_ROUTING_KEY_SMALL_JOBS', DEFAULT_PRIORITY_QUEUE)

# Queue to use for expiring old entitlements
ENTITLEMENTS_EXPIRATION_ROUTING_KEY = ENV_TOKENS.get('ENTITLEMENTS_EXPIRATION_ROUTING_KEY', DEFAULT_PRIORITY_QUEUE)

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

# following setting is for backward compatibility
if ENV_TOKENS.get('COMPREHENSIVE_THEME_DIR', None):
    COMPREHENSIVE_THEME_DIR = ENV_TOKENS.get('COMPREHENSIVE_THEME_DIR')

COMPREHENSIVE_THEME_DIRS = ENV_TOKENS.get('COMPREHENSIVE_THEME_DIRS', COMPREHENSIVE_THEME_DIRS) or []

# COMPREHENSIVE_THEME_LOCALE_PATHS contain the paths to themes locale directories e.g.
# "COMPREHENSIVE_THEME_LOCALE_PATHS" : [
#        "/edx/src/edx-themes/conf/locale"
#    ],
COMPREHENSIVE_THEME_LOCALE_PATHS = ENV_TOKENS.get('COMPREHENSIVE_THEME_LOCALE_PATHS', [])

DEFAULT_SITE_THEME = ENV_TOKENS.get('DEFAULT_SITE_THEME', DEFAULT_SITE_THEME)
ENABLE_COMPREHENSIVE_THEMING = ENV_TOKENS.get('ENABLE_COMPREHENSIVE_THEMING', ENABLE_COMPREHENSIVE_THEMING)

# Marketing link overrides
MKTG_URL_LINK_MAP.update(ENV_TOKENS.get('MKTG_URL_LINK_MAP', {}))

# Intentional defaults.
SUPPORT_SITE_LINK = ENV_TOKENS.get('SUPPORT_SITE_LINK', SUPPORT_SITE_LINK)
ID_VERIFICATION_SUPPORT_LINK = ENV_TOKENS.get('ID_VERIFICATION_SUPPORT_LINK', SUPPORT_SITE_LINK)
PASSWORD_RESET_SUPPORT_LINK = ENV_TOKENS.get('PASSWORD_RESET_SUPPORT_LINK', SUPPORT_SITE_LINK)
ACTIVATION_EMAIL_SUPPORT_LINK = ENV_TOKENS.get(
    'ACTIVATION_EMAIL_SUPPORT_LINK', SUPPORT_SITE_LINK
)

# Mobile store URL overrides
MOBILE_STORE_URLS = ENV_TOKENS.get('MOBILE_STORE_URLS', MOBILE_STORE_URLS)

# Timezone overrides
TIME_ZONE = ENV_TOKENS.get('TIME_ZONE', TIME_ZONE)

# Translation overrides
LANGUAGES = ENV_TOKENS.get('LANGUAGES', LANGUAGES)
CERTIFICATE_TEMPLATE_LANGUAGES = ENV_TOKENS.get('CERTIFICATE_TEMPLATE_LANGUAGES', CERTIFICATE_TEMPLATE_LANGUAGES)
LANGUAGE_DICT = dict(LANGUAGES)
LANGUAGE_CODE = ENV_TOKENS.get('LANGUAGE_CODE', LANGUAGE_CODE)
LANGUAGE_COOKIE = ENV_TOKENS.get('LANGUAGE_COOKIE', LANGUAGE_COOKIE)
ALL_LANGUAGES = ENV_TOKENS.get('ALL_LANGUAGES', ALL_LANGUAGES)

USE_I18N = ENV_TOKENS.get('USE_I18N', USE_I18N)

# Additional installed apps
for app in ENV_TOKENS.get('ADDL_INSTALLED_APPS', []):
    INSTALLED_APPS.append(app)

WIKI_ENABLED = ENV_TOKENS.get('WIKI_ENABLED', WIKI_ENABLED)

local_loglevel = ENV_TOKENS.get('LOCAL_LOGLEVEL', 'INFO')
LOG_DIR = ENV_TOKENS['LOG_DIR']
DATA_DIR = path(ENV_TOKENS.get('DATA_DIR', DATA_DIR))

LOGGING = get_logger_config(LOG_DIR,
                            logging_env=ENV_TOKENS['LOGGING_ENV'],
                            local_loglevel=local_loglevel,
                            service_variant=SERVICE_VARIANT)

COURSE_LISTINGS = ENV_TOKENS.get('COURSE_LISTINGS', {})
COMMENTS_SERVICE_URL = ENV_TOKENS.get("COMMENTS_SERVICE_URL", '')
COMMENTS_SERVICE_KEY = ENV_TOKENS.get("COMMENTS_SERVICE_KEY", '')
CERT_NAME_SHORT = ENV_TOKENS.get('CERT_NAME_SHORT', CERT_NAME_SHORT)
CERT_NAME_LONG = ENV_TOKENS.get('CERT_NAME_LONG', CERT_NAME_LONG)
CERT_QUEUE = ENV_TOKENS.get("CERT_QUEUE", 'test-pull')
ZENDESK_URL = ENV_TOKENS.get('ZENDESK_URL', ZENDESK_URL)
ZENDESK_CUSTOM_FIELDS = ENV_TOKENS.get('ZENDESK_CUSTOM_FIELDS', ZENDESK_CUSTOM_FIELDS)

FEEDBACK_SUBMISSION_EMAIL = ENV_TOKENS.get("FEEDBACK_SUBMISSION_EMAIL")
MKTG_URLS = ENV_TOKENS.get('MKTG_URLS', MKTG_URLS)

# Badgr API
BADGR_API_TOKEN = ENV_TOKENS.get('BADGR_API_TOKEN', BADGR_API_TOKEN)
BADGR_BASE_URL = ENV_TOKENS.get('BADGR_BASE_URL', BADGR_BASE_URL)
BADGR_ISSUER_SLUG = ENV_TOKENS.get('BADGR_ISSUER_SLUG', BADGR_ISSUER_SLUG)
BADGR_TIMEOUT = ENV_TOKENS.get('BADGR_TIMEOUT', BADGR_TIMEOUT)

# git repo loading  environment
GIT_REPO_DIR = ENV_TOKENS.get('GIT_REPO_DIR', '/edx/var/edxapp/course_repos')
GIT_IMPORT_STATIC = ENV_TOKENS.get('GIT_IMPORT_STATIC', True)
GIT_IMPORT_PYTHON_LIB = ENV_TOKENS.get('GIT_IMPORT_PYTHON_LIB', True)
PYTHON_LIB_FILENAME = ENV_TOKENS.get('PYTHON_LIB_FILENAME', 'python_lib.zip')

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
SSL_AUTH_DN_FORMAT_STRING = ENV_TOKENS.get(
    "SSL_AUTH_DN_FORMAT_STRING",
    "/C=US/ST=Massachusetts/O=Massachusetts Institute of Technology/OU=Client CA v1/CN={0}/emailAddress={1}"
)

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

# Video Caching. Pairing country codes with CDN URLs.
# Example: {'CN': 'http://api.xuetangx.com/edx/video?s3_url='}
VIDEO_CDN_URL = ENV_TOKENS.get('VIDEO_CDN_URL', {})

# Branded footer
FOOTER_OPENEDX_URL = ENV_TOKENS.get('FOOTER_OPENEDX_URL', FOOTER_OPENEDX_URL)
FOOTER_OPENEDX_LOGO_IMAGE = ENV_TOKENS.get('FOOTER_OPENEDX_LOGO_IMAGE', FOOTER_OPENEDX_LOGO_IMAGE)
FOOTER_ORGANIZATION_IMAGE = ENV_TOKENS.get('FOOTER_ORGANIZATION_IMAGE', FOOTER_ORGANIZATION_IMAGE)
FOOTER_CACHE_TIMEOUT = ENV_TOKENS.get('FOOTER_CACHE_TIMEOUT', FOOTER_CACHE_TIMEOUT)
FOOTER_BROWSER_CACHE_MAX_AGE = ENV_TOKENS.get('FOOTER_BROWSER_CACHE_MAX_AGE', FOOTER_BROWSER_CACHE_MAX_AGE)

# Credit notifications settings
NOTIFICATION_EMAIL_CSS = ENV_TOKENS.get('NOTIFICATION_EMAIL_CSS', NOTIFICATION_EMAIL_CSS)
NOTIFICATION_EMAIL_EDX_LOGO = ENV_TOKENS.get('NOTIFICATION_EMAIL_EDX_LOGO', NOTIFICATION_EMAIL_EDX_LOGO)

# Determines whether the CSRF token can be transported on
# unencrypted channels. It is set to False here for backward compatibility,
# but it is highly recommended that this is True for enviroments accessed
# by end users.
CSRF_COOKIE_SECURE = ENV_TOKENS.get('CSRF_COOKIE_SECURE', False)

# Whitelist of domains to which the login/logout pages will redirect.
LOGIN_REDIRECT_WHITELIST = ENV_TOKENS.get('LOGIN_REDIRECT_WHITELIST', LOGIN_REDIRECT_WHITELIST)

############# CORS headers for cross-domain requests #################

if FEATURES.get('ENABLE_CORS_HEADERS') or FEATURES.get('ENABLE_CROSS_DOMAIN_CSRF_COOKIE'):
    CORS_ALLOW_CREDENTIALS = True
    CORS_ORIGIN_WHITELIST = ENV_TOKENS.get('CORS_ORIGIN_WHITELIST', ())
    CORS_ORIGIN_ALLOW_ALL = ENV_TOKENS.get('CORS_ORIGIN_ALLOW_ALL', False)
    CORS_ALLOW_INSECURE = ENV_TOKENS.get('CORS_ALLOW_INSECURE', False)
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


# Field overrides. To use the IDDE feature, add
# 'lms.djangoapps.courseware.student_field_overrides.IndividualStudentOverrideProvider'.
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
# PREVIEW DOMAIN must be present in HOSTNAME_MODULESTORE_DEFAULT_MAPPINGS for the preview to show draft changes
if 'PREVIEW_LMS_BASE' in FEATURES and FEATURES['PREVIEW_LMS_BASE'] != '':
    PREVIEW_DOMAIN = FEATURES['PREVIEW_LMS_BASE'].split(':')[0]
    # update dictionary with preview domain regex
    HOSTNAME_MODULESTORE_DEFAULT_MAPPINGS.update({
        PREVIEW_DOMAIN: 'draft-preferred'
    })

MODULESTORE_FIELD_OVERRIDE_PROVIDERS = ENV_TOKENS.get(
    'MODULESTORE_FIELD_OVERRIDE_PROVIDERS',
    MODULESTORE_FIELD_OVERRIDE_PROVIDERS
)

XBLOCK_FIELD_DATA_WRAPPERS = ENV_TOKENS.get(
    'XBLOCK_FIELD_DATA_WRAPPERS',
    XBLOCK_FIELD_DATA_WRAPPERS
)

############### Mixed Related(Secure/Not-Secure) Items ##########
LMS_SEGMENT_KEY = AUTH_TOKENS.get('SEGMENT_KEY')

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

# Disabling querystring auth instructs Boto to exclude the querystring parameters (e.g. signature, access key) it
# normally appends to every returned URL.
AWS_QUERYSTRING_AUTH = AUTH_TOKENS.get('AWS_QUERYSTRING_AUTH', True)
AWS_S3_CUSTOM_DOMAIN = AUTH_TOKENS.get('AWS_S3_CUSTOM_DOMAIN', 'edxuploads.s3.amazonaws.com')

if AUTH_TOKENS.get('DEFAULT_FILE_STORAGE'):
    DEFAULT_FILE_STORAGE = AUTH_TOKENS.get('DEFAULT_FILE_STORAGE')
elif AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
else:
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Specific setting for the File Upload Service to store media in a bucket.
FILE_UPLOAD_STORAGE_BUCKET_NAME = ENV_TOKENS.get('FILE_UPLOAD_STORAGE_BUCKET_NAME', FILE_UPLOAD_STORAGE_BUCKET_NAME)
FILE_UPLOAD_STORAGE_PREFIX = ENV_TOKENS.get('FILE_UPLOAD_STORAGE_PREFIX', FILE_UPLOAD_STORAGE_PREFIX)

# If there is a database called 'read_replica', you can use the use_read_replica_if_available
# function in util/query.py, which is useful for very large database reads
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

XQUEUE_INTERFACE = AUTH_TOKENS['XQUEUE_INTERFACE']

# Get the MODULESTORE from auth.json, but if it doesn't exist,
# use the one from common.py
MODULESTORE = convert_module_store_setting_if_needed(AUTH_TOKENS.get('MODULESTORE', MODULESTORE))
CONTENTSTORE = AUTH_TOKENS.get('CONTENTSTORE', CONTENTSTORE)
DOC_STORE_CONFIG = AUTH_TOKENS.get('DOC_STORE_CONFIG', DOC_STORE_CONFIG)
MONGODB_LOG = AUTH_TOKENS.get('MONGODB_LOG', {})

EMAIL_HOST_USER = AUTH_TOKENS.get('EMAIL_HOST_USER', '')  # django default is ''
EMAIL_HOST_PASSWORD = AUTH_TOKENS.get('EMAIL_HOST_PASSWORD', '')  # django default is ''

# Datadog for events!
DATADOG = AUTH_TOKENS.get("DATADOG", {})
DATADOG.update(ENV_TOKENS.get("DATADOG", {}))

# TODO: deprecated (compatibility with previous settings)
if 'DATADOG_API' in AUTH_TOKENS:
    DATADOG['api_key'] = AUTH_TOKENS['DATADOG_API']

# Analytics API
ANALYTICS_API_KEY = AUTH_TOKENS.get("ANALYTICS_API_KEY", ANALYTICS_API_KEY)
ANALYTICS_API_URL = ENV_TOKENS.get("ANALYTICS_API_URL", ANALYTICS_API_URL)

# Mailchimp New User List
MAILCHIMP_NEW_USER_LIST_ID = ENV_TOKENS.get("MAILCHIMP_NEW_USER_LIST_ID")

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
BROKER_USE_SSL = ENV_TOKENS.get('CELERY_BROKER_USE_SSL', False)

# Block Structures
BLOCK_STRUCTURES_SETTINGS = ENV_TOKENS.get('BLOCK_STRUCTURES_SETTINGS', BLOCK_STRUCTURES_SETTINGS)

# upload limits
STUDENT_FILEUPLOAD_MAX_SIZE = ENV_TOKENS.get("STUDENT_FILEUPLOAD_MAX_SIZE", STUDENT_FILEUPLOAD_MAX_SIZE)

# Event tracking
TRACKING_BACKENDS.update(AUTH_TOKENS.get("TRACKING_BACKENDS", {}))
EVENT_TRACKING_BACKENDS['tracking_logs']['OPTIONS']['backends'].update(AUTH_TOKENS.get("EVENT_TRACKING_BACKENDS", {}))
EVENT_TRACKING_BACKENDS['segmentio']['OPTIONS']['processors'][0]['OPTIONS']['whitelist'].extend(
    AUTH_TOKENS.get("EVENT_TRACKING_SEGMENTIO_EMIT_WHITELIST", []))
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

# Heartbeat
HEARTBEAT_CHECKS = ENV_TOKENS.get('HEARTBEAT_CHECKS', HEARTBEAT_CHECKS)
HEARTBEAT_EXTENDED_CHECKS = ENV_TOKENS.get('HEARTBEAT_EXTENDED_CHECKS', HEARTBEAT_EXTENDED_CHECKS)
HEARTBEAT_CELERY_TIMEOUT = ENV_TOKENS.get('HEARTBEAT_CELERY_TIMEOUT', HEARTBEAT_CELERY_TIMEOUT)

# Student identity verification settings
VERIFY_STUDENT = AUTH_TOKENS.get("VERIFY_STUDENT", VERIFY_STUDENT)
DISABLE_ACCOUNT_ACTIVATION_REQUIREMENT_SWITCH = ENV_TOKENS.get(
    "DISABLE_ACCOUNT_ACTIVATION_REQUIREMENT_SWITCH",
    DISABLE_ACCOUNT_ACTIVATION_REQUIREMENT_SWITCH
)

# Grades download
GRADES_DOWNLOAD_ROUTING_KEY = ENV_TOKENS.get('GRADES_DOWNLOAD_ROUTING_KEY', HIGH_MEM_QUEUE)

GRADES_DOWNLOAD = ENV_TOKENS.get("GRADES_DOWNLOAD", GRADES_DOWNLOAD)

# Rate limit for regrading tasks that a grading policy change can kick off
POLICY_CHANGE_TASK_RATE_LIMIT = ENV_TOKENS.get('POLICY_CHANGE_TASK_RATE_LIMIT', POLICY_CHANGE_TASK_RATE_LIMIT)

# financial reports
FINANCIAL_REPORTS = ENV_TOKENS.get("FINANCIAL_REPORTS", FINANCIAL_REPORTS)

##### ORA2 ######
# Prefix for uploads of example-based assessment AI classifiers
# This can be used to separate uploads for different environments
# within the same S3 bucket.
ORA2_FILE_PREFIX = ENV_TOKENS.get("ORA2_FILE_PREFIX", ORA2_FILE_PREFIX)

##### ACCOUNT LOCKOUT DEFAULT PARAMETERS #####
MAX_FAILED_LOGIN_ATTEMPTS_ALLOWED = ENV_TOKENS.get("MAX_FAILED_LOGIN_ATTEMPTS_ALLOWED", 5)
MAX_FAILED_LOGIN_ATTEMPTS_LOCKOUT_PERIOD_SECS = ENV_TOKENS.get("MAX_FAILED_LOGIN_ATTEMPTS_LOCKOUT_PERIOD_SECS", 15 * 60)

#### PASSWORD POLICY SETTINGS #####
AUTH_PASSWORD_VALIDATORS = ENV_TOKENS.get("AUTH_PASSWORD_VALIDATORS", AUTH_PASSWORD_VALIDATORS)

### INACTIVITY SETTINGS ####
SESSION_INACTIVITY_TIMEOUT_IN_SECONDS = AUTH_TOKENS.get("SESSION_INACTIVITY_TIMEOUT_IN_SECONDS")

##### LMS DEADLINE DISPLAY TIME_ZONE #######
TIME_ZONE_DISPLAYED_FOR_DEADLINES = ENV_TOKENS.get("TIME_ZONE_DISPLAYED_FOR_DEADLINES",
                                                   TIME_ZONE_DISPLAYED_FOR_DEADLINES)

##### X-Frame-Options response header settings #####
X_FRAME_OPTIONS = ENV_TOKENS.get('X_FRAME_OPTIONS', X_FRAME_OPTIONS)

##### Third-party auth options ################################################
if FEATURES.get('ENABLE_THIRD_PARTY_AUTH'):
    tmp_backends = ENV_TOKENS.get('THIRD_PARTY_AUTH_BACKENDS', [
        'social_core.backends.google.GoogleOAuth2',
        'social_core.backends.linkedin.LinkedinOAuth2',
        'social_core.backends.facebook.FacebookOAuth2',
        'social_core.backends.azuread.AzureADOAuth2',
        'third_party_auth.saml.SAMLAuthBackend',
        'third_party_auth.lti.LTIAuthBackend',
    ])

    AUTHENTICATION_BACKENDS = list(tmp_backends) + list(AUTHENTICATION_BACKENDS)
    del tmp_backends

    # The reduced session expiry time during the third party login pipeline. (Value in seconds)
    SOCIAL_AUTH_PIPELINE_TIMEOUT = ENV_TOKENS.get('SOCIAL_AUTH_PIPELINE_TIMEOUT', 600)

    # Most provider configuration is done via ConfigurationModels but for a few sensitive values
    # we allow configuration via AUTH_TOKENS instead (optionally).
    # The SAML private/public key values do not need the delimiter lines (such as
    # "-----BEGIN PRIVATE KEY-----", "-----END PRIVATE KEY-----" etc.) but they may be included
    # if you want (though it's easier to format the key values as JSON without the delimiters).
    SOCIAL_AUTH_SAML_SP_PRIVATE_KEY = AUTH_TOKENS.get('SOCIAL_AUTH_SAML_SP_PRIVATE_KEY', '')
    SOCIAL_AUTH_SAML_SP_PUBLIC_CERT = AUTH_TOKENS.get('SOCIAL_AUTH_SAML_SP_PUBLIC_CERT', '')
    SOCIAL_AUTH_SAML_SP_PRIVATE_KEY_DICT = AUTH_TOKENS.get('SOCIAL_AUTH_SAML_SP_PRIVATE_KEY_DICT', {})
    SOCIAL_AUTH_SAML_SP_PUBLIC_CERT_DICT = AUTH_TOKENS.get('SOCIAL_AUTH_SAML_SP_PUBLIC_CERT_DICT', {})
    SOCIAL_AUTH_OAUTH_SECRETS = AUTH_TOKENS.get('SOCIAL_AUTH_OAUTH_SECRETS', {})
    SOCIAL_AUTH_LTI_CONSUMER_SECRETS = AUTH_TOKENS.get('SOCIAL_AUTH_LTI_CONSUMER_SECRETS', {})

    # third_party_auth config moved to ConfigurationModels. This is for data migration only:
    THIRD_PARTY_AUTH_OLD_CONFIG = AUTH_TOKENS.get('THIRD_PARTY_AUTH', None)

    if ENV_TOKENS.get('THIRD_PARTY_AUTH_SAML_FETCH_PERIOD_HOURS', 24) is not None:
        CELERYBEAT_SCHEDULE['refresh-saml-metadata'] = {
            'task': 'third_party_auth.fetch_saml_metadata',
            'schedule': datetime.timedelta(hours=ENV_TOKENS.get('THIRD_PARTY_AUTH_SAML_FETCH_PERIOD_HOURS', 24)),
        }

    # The following can be used to integrate a custom login form with third_party_auth.
    # It should be a dict where the key is a word passed via ?auth_entry=, and the value is a
    # dict with an arbitrary 'secret_key' and a 'url'.
    THIRD_PARTY_AUTH_CUSTOM_AUTH_FORMS = AUTH_TOKENS.get('THIRD_PARTY_AUTH_CUSTOM_AUTH_FORMS', {})

    # Whether to allow unprivileged users to discover SSO providers for arbitrary usernames.
    ALLOW_UNPRIVILEGED_SSO_PROVIDER_QUERY = ENV_TOKENS.get('ALLOW_UNPRIVILEGED_SSO_PROVIDER_QUERY', False)

##### OAUTH2 Provider ##############
if FEATURES.get('ENABLE_OAUTH2_PROVIDER'):
    OAUTH_OIDC_ISSUER = ENV_TOKENS['OAUTH_OIDC_ISSUER']
    OAUTH_ENFORCE_SECURE = ENV_TOKENS.get('OAUTH_ENFORCE_SECURE', True)
    OAUTH_ENFORCE_CLIENT_SECURE = ENV_TOKENS.get('OAUTH_ENFORCE_CLIENT_SECURE', True)
    # Defaults for the following are defined in lms.envs.common
    OAUTH_EXPIRE_DELTA = datetime.timedelta(
        days=ENV_TOKENS.get('OAUTH_EXPIRE_CONFIDENTIAL_CLIENT_DAYS', OAUTH_EXPIRE_CONFIDENTIAL_CLIENT_DAYS)
    )
    OAUTH_EXPIRE_DELTA_PUBLIC = datetime.timedelta(
        days=ENV_TOKENS.get('OAUTH_EXPIRE_PUBLIC_CLIENT_DAYS', OAUTH_EXPIRE_PUBLIC_CLIENT_DAYS)
    )
    OAUTH_ID_TOKEN_EXPIRATION = ENV_TOKENS.get('OAUTH_ID_TOKEN_EXPIRATION', OAUTH_ID_TOKEN_EXPIRATION)
    OAUTH_DELETE_EXPIRED = ENV_TOKENS.get('OAUTH_DELETE_EXPIRED', OAUTH_DELETE_EXPIRED)

##### THIRD_PARTY_AUTH #############
TPA_PROVIDER_BURST_THROTTLE = ENV_TOKENS.get('TPA_PROVIDER_BURST_THROTTLE', TPA_PROVIDER_BURST_THROTTLE)
TPA_PROVIDER_SUSTAINED_THROTTLE = ENV_TOKENS.get('TPA_PROVIDER_SUSTAINED_THROTTLE', TPA_PROVIDER_SUSTAINED_THROTTLE)

##### GOOGLE ANALYTICS IDS #####
GOOGLE_ANALYTICS_ACCOUNT = AUTH_TOKENS.get('GOOGLE_ANALYTICS_ACCOUNT')
GOOGLE_ANALYTICS_TRACKING_ID = AUTH_TOKENS.get('GOOGLE_ANALYTICS_TRACKING_ID')
GOOGLE_ANALYTICS_LINKEDIN = AUTH_TOKENS.get('GOOGLE_ANALYTICS_LINKEDIN')
GOOGLE_SITE_VERIFICATION_ID = ENV_TOKENS.get('GOOGLE_SITE_VERIFICATION_ID')

##### BRANCH.IO KEY #####
BRANCH_IO_KEY = AUTH_TOKENS.get('BRANCH_IO_KEY')

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

if FEATURES.get('ENABLE_COURSEWARE_SEARCH') or \
   FEATURES.get('ENABLE_DASHBOARD_SEARCH') or \
   FEATURES.get('ENABLE_COURSE_DISCOVERY') or \
   FEATURES.get('ENABLE_TEAMS'):
    # Use ElasticSearch as the search engine herein
    SEARCH_ENGINE = "search.elastic.ElasticSearchEngine"

ELASTIC_SEARCH_CONFIG = ENV_TOKENS.get('ELASTIC_SEARCH_CONFIG', [{}])

# Facebook app
FACEBOOK_API_VERSION = AUTH_TOKENS.get("FACEBOOK_API_VERSION")
FACEBOOK_APP_SECRET = AUTH_TOKENS.get("FACEBOOK_APP_SECRET")
FACEBOOK_APP_ID = AUTH_TOKENS.get("FACEBOOK_APP_ID")

XBLOCK_SETTINGS = ENV_TOKENS.get('XBLOCK_SETTINGS', {})
XBLOCK_SETTINGS.setdefault("VideoDescriptor", {})["licensing_enabled"] = FEATURES.get("LICENSING", False)
XBLOCK_SETTINGS.setdefault("VideoModule", {})['YOUTUBE_API_KEY'] = AUTH_TOKENS.get('YOUTUBE_API_KEY', YOUTUBE_API_KEY)

##### VIDEO IMAGE STORAGE #####
VIDEO_IMAGE_SETTINGS = ENV_TOKENS.get('VIDEO_IMAGE_SETTINGS', VIDEO_IMAGE_SETTINGS)

##### VIDEO TRANSCRIPTS STORAGE #####
VIDEO_TRANSCRIPTS_SETTINGS = ENV_TOKENS.get('VIDEO_TRANSCRIPTS_SETTINGS', VIDEO_TRANSCRIPTS_SETTINGS)

##### ECOMMERCE API CONFIGURATION SETTINGS #####
ECOMMERCE_PUBLIC_URL_ROOT = ENV_TOKENS.get('ECOMMERCE_PUBLIC_URL_ROOT', ECOMMERCE_PUBLIC_URL_ROOT)
ECOMMERCE_API_URL = ENV_TOKENS.get('ECOMMERCE_API_URL', ECOMMERCE_API_URL)
ECOMMERCE_API_TIMEOUT = ENV_TOKENS.get('ECOMMERCE_API_TIMEOUT', ECOMMERCE_API_TIMEOUT)

COURSE_CATALOG_API_URL = ENV_TOKENS.get('COURSE_CATALOG_API_URL', COURSE_CATALOG_API_URL)

ECOMMERCE_SERVICE_WORKER_USERNAME = ENV_TOKENS.get(
    'ECOMMERCE_SERVICE_WORKER_USERNAME',
    ECOMMERCE_SERVICE_WORKER_USERNAME
)

##### Custom Courses for EdX #####
if FEATURES.get('CUSTOM_COURSES_EDX'):
    INSTALLED_APPS += ['lms.djangoapps.ccx', 'openedx.core.djangoapps.ccxcon.apps.CCXConnectorConfig']
    MODULESTORE_FIELD_OVERRIDE_PROVIDERS += (
        'lms.djangoapps.ccx.overrides.CustomCoursesForEdxOverrideProvider',
    )
CCX_MAX_STUDENTS_ALLOWED = ENV_TOKENS.get('CCX_MAX_STUDENTS_ALLOWED', CCX_MAX_STUDENTS_ALLOWED)

##### Individual Due Date Extensions #####
if FEATURES.get('INDIVIDUAL_DUE_DATES'):
    FIELD_OVERRIDE_PROVIDERS += (
        'lms.djangoapps.courseware.student_field_overrides.IndividualStudentOverrideProvider',
    )

##### Self-Paced Course Due Dates #####
XBLOCK_FIELD_DATA_WRAPPERS += (
    'lms.djangoapps.courseware.field_overrides:OverrideModulestoreFieldData.wrap',
)

MODULESTORE_FIELD_OVERRIDE_PROVIDERS += (
    'courseware.self_paced_overrides.SelfPacedDateOverrideProvider',
)

# PROFILE IMAGE CONFIG
PROFILE_IMAGE_BACKEND = ENV_TOKENS.get('PROFILE_IMAGE_BACKEND', PROFILE_IMAGE_BACKEND)
PROFILE_IMAGE_SECRET_KEY = AUTH_TOKENS.get('PROFILE_IMAGE_SECRET_KEY', PROFILE_IMAGE_SECRET_KEY)
PROFILE_IMAGE_MAX_BYTES = ENV_TOKENS.get('PROFILE_IMAGE_MAX_BYTES', PROFILE_IMAGE_MAX_BYTES)
PROFILE_IMAGE_MIN_BYTES = ENV_TOKENS.get('PROFILE_IMAGE_MIN_BYTES', PROFILE_IMAGE_MIN_BYTES)
PROFILE_IMAGE_DEFAULT_FILENAME = 'images/profiles/default'
PROFILE_IMAGE_SIZES_MAP = ENV_TOKENS.get(
    'PROFILE_IMAGE_SIZES_MAP',
    PROFILE_IMAGE_SIZES_MAP
)

# EdxNotes config

EDXNOTES_PUBLIC_API = ENV_TOKENS.get('EDXNOTES_PUBLIC_API', EDXNOTES_PUBLIC_API)
EDXNOTES_INTERNAL_API = ENV_TOKENS.get('EDXNOTES_INTERNAL_API', EDXNOTES_INTERNAL_API)

EDXNOTES_CONNECT_TIMEOUT = ENV_TOKENS.get('EDXNOTES_CONNECT_TIMEOUT', EDXNOTES_CONNECT_TIMEOUT)
EDXNOTES_READ_TIMEOUT = ENV_TOKENS.get('EDXNOTES_READ_TIMEOUT', EDXNOTES_READ_TIMEOUT)

##### Credit Provider Integration #####

CREDIT_PROVIDER_SECRET_KEYS = AUTH_TOKENS.get("CREDIT_PROVIDER_SECRET_KEYS", {})

##################### LTI Provider #####################
if FEATURES.get('ENABLE_LTI_PROVIDER'):
    INSTALLED_APPS.append('lti_provider.apps.LtiProviderConfig')
    AUTHENTICATION_BACKENDS.append('lti_provider.users.LtiBackend')

LTI_USER_EMAIL_DOMAIN = ENV_TOKENS.get('LTI_USER_EMAIL_DOMAIN', 'lti.example.com')

# For more info on this, see the notes in common.py
LTI_AGGREGATE_SCORE_PASSBACK_DELAY = ENV_TOKENS.get(
    'LTI_AGGREGATE_SCORE_PASSBACK_DELAY', LTI_AGGREGATE_SCORE_PASSBACK_DELAY
)

##################### Credit Provider help link ####################
CREDIT_HELP_LINK_URL = ENV_TOKENS.get('CREDIT_HELP_LINK_URL', CREDIT_HELP_LINK_URL)

#### JWT configuration ####
JWT_AUTH.update(ENV_TOKENS.get('JWT_AUTH', {}))
JWT_AUTH.update(AUTH_TOKENS.get('JWT_AUTH', {}))

################# MICROSITE ####################
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

# Offset for pk of courseware.StudentModuleHistoryExtended
STUDENTMODULEHISTORYEXTENDED_OFFSET = ENV_TOKENS.get(
    'STUDENTMODULEHISTORYEXTENDED_OFFSET', STUDENTMODULEHISTORYEXTENDED_OFFSET
)

# Cutoff date for granting audit certificates
if ENV_TOKENS.get('AUDIT_CERT_CUTOFF_DATE', None):
    AUDIT_CERT_CUTOFF_DATE = dateutil.parser.parse(ENV_TOKENS.get('AUDIT_CERT_CUTOFF_DATE'))

################################ Settings for Credentials Service ################################

CREDENTIALS_GENERATION_ROUTING_KEY = ENV_TOKENS.get('CREDENTIALS_GENERATION_ROUTING_KEY', DEFAULT_PRIORITY_QUEUE)

# The extended StudentModule history table
if FEATURES.get('ENABLE_CSMH_EXTENDED'):
    INSTALLED_APPS.append('coursewarehistoryextended')

API_ACCESS_MANAGER_EMAIL = ENV_TOKENS.get('API_ACCESS_MANAGER_EMAIL')
API_ACCESS_FROM_EMAIL = ENV_TOKENS.get('API_ACCESS_FROM_EMAIL')

# Mobile App Version Upgrade config
APP_UPGRADE_CACHE_TIMEOUT = ENV_TOKENS.get('APP_UPGRADE_CACHE_TIMEOUT', APP_UPGRADE_CACHE_TIMEOUT)

AFFILIATE_COOKIE_NAME = ENV_TOKENS.get('AFFILIATE_COOKIE_NAME', AFFILIATE_COOKIE_NAME)

############## Settings for LMS Context Sensitive Help ##############

HELP_TOKENS_BOOKS = ENV_TOKENS.get('HELP_TOKENS_BOOKS', HELP_TOKENS_BOOKS)


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

# A shared secret to be used for encrypting passwords passed from the enterprise api
# to the enteprise reporting script.
ENTERPRISE_REPORTING_SECRET = AUTH_TOKENS.get(
    'ENTERPRISE_REPORTING_SECRET',
    ENTERPRISE_REPORTING_SECRET
)

# A default dictionary to be used for filtering out enterprise customer catalog.
ENTERPRISE_CUSTOMER_CATALOG_DEFAULT_CONTENT_FILTER = ENV_TOKENS.get(
    'ENTERPRISE_CUSTOMER_CATALOG_DEFAULT_CONTENT_FILTER',
    ENTERPRISE_CUSTOMER_CATALOG_DEFAULT_CONTENT_FILTER
)

############## ENTERPRISE SERVICE API CLIENT CONFIGURATION ######################
# The LMS communicates with the Enterprise service via the EdxRestApiClient class
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

############## CATALOG/DISCOVERY SERVICE API CLIENT CONFIGURATION ######################
# The LMS communicates with the Catalog service via the EdxRestApiClient class
# The below environmental settings are utilized by the LMS when interacting with
# the service, and override the default parameters which are defined in common.py

COURSES_API_CACHE_TIMEOUT = ENV_TOKENS.get('COURSES_API_CACHE_TIMEOUT', COURSES_API_CACHE_TIMEOUT)

# Add an ICP license for serving content in China if your organization is registered to do so
ICP_LICENSE = ENV_TOKENS.get('ICP_LICENSE', None)

############## Settings for CourseGraph ############################
COURSEGRAPH_JOB_QUEUE = ENV_TOKENS.get('COURSEGRAPH_JOB_QUEUE', DEFAULT_PRIORITY_QUEUE)

########################## Parental controls config  #######################

# The age at which a learner no longer requires parental consent, or None
# if parental consent is never required.
PARENTAL_CONSENT_AGE_LIMIT = ENV_TOKENS.get(
    'PARENTAL_CONSENT_AGE_LIMIT',
    PARENTAL_CONSENT_AGE_LIMIT
)

# Do NOT calculate this dynamically at startup with git because it's *slow*.
EDX_PLATFORM_REVISION = ENV_TOKENS.get('EDX_PLATFORM_REVISION', EDX_PLATFORM_REVISION)

########################## Extra middleware classes  #######################

# Allow extra middleware classes to be added to the app through configuration.
MIDDLEWARE_CLASSES.extend(ENV_TOKENS.get('EXTRA_MIDDLEWARE_CLASSES', []))

########################## Settings for Completion API #####################

# Once a user has watched this percentage of a video, mark it as complete:
# (0.0 = 0%, 1.0 = 100%)
COMPLETION_VIDEO_COMPLETE_PERCENTAGE = ENV_TOKENS.get(
    'COMPLETION_VIDEO_COMPLETE_PERCENTAGE',
    COMPLETION_VIDEO_COMPLETE_PERCENTAGE,
)
# The time a block needs to be viewed to be considered complete, in milliseconds.
COMPLETION_BY_VIEWING_DELAY_MS = ENV_TOKENS.get('COMPLETION_BY_VIEWING_DELAY_MS', COMPLETION_BY_VIEWING_DELAY_MS)

############### Settings for django-fernet-fields ##################
FERNET_KEYS = AUTH_TOKENS.get('FERNET_KEYS', FERNET_KEYS)

################# Settings for the maintenance banner #################
MAINTENANCE_BANNER_TEXT = ENV_TOKENS.get('MAINTENANCE_BANNER_TEXT', None)

############### Settings for Retirement #####################
RETIRED_USERNAME_PREFIX = ENV_TOKENS.get('RETIRED_USERNAME_PREFIX', RETIRED_USERNAME_PREFIX)
RETIRED_EMAIL_PREFIX = ENV_TOKENS.get('RETIRED_EMAIL_PREFIX', RETIRED_EMAIL_PREFIX)
RETIRED_EMAIL_DOMAIN = ENV_TOKENS.get('RETIRED_EMAIL_DOMAIN', RETIRED_EMAIL_DOMAIN)
RETIRED_USER_SALTS = ENV_TOKENS.get('RETIRED_USER_SALTS', RETIRED_USER_SALTS)
RETIREMENT_SERVICE_WORKER_USERNAME = ENV_TOKENS.get(
    'RETIREMENT_SERVICE_WORKER_USERNAME',
    RETIREMENT_SERVICE_WORKER_USERNAME
)
RETIREMENT_STATES = ENV_TOKENS.get('RETIREMENT_STATES', RETIREMENT_STATES)

############## Settings for Course Enrollment Modes ######################
COURSE_ENROLLMENT_MODES = ENV_TOKENS.get('COURSE_ENROLLMENT_MODES', COURSE_ENROLLMENT_MODES)

############## Settings for Writable Gradebook  #########################
WRITABLE_GRADEBOOK_URL = ENV_TOKENS.get('WRITABLE_GRADEBOOK_URL', WRITABLE_GRADEBOOK_URL)

############################### Plugin Settings ###############################

# This is at the bottom because it is going to load more settings after base settings are loaded
from openedx.core.djangoapps.plugins import plugin_settings, constants as plugin_constants  # pylint: disable=wrong-import-order, wrong-import-position
plugin_settings.add_plugins(__name__, plugin_constants.ProjectType.LMS, plugin_constants.SettingsType.AWS)

########################## Derive Any Derived Settings  #######################

derive_settings(__name__)

logging.warn('DEPRECATION WARNING: aws.py has been deprecated, you should use production.py instead.')
