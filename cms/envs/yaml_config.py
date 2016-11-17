"""
This is the default template for our main set of AWS servers.

Before importing this settings file the following MUST be
defined in the environment:

    * SERVICE_VARIANT - can be either "lms" or "cms"
    * CONFIG_ROOT - the directory where the application
                    yaml config files are located

"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=wildcard-import, unused-wildcard-import, undefined-variable, used-before-assignment

import yaml

from .common import *
from openedx.core.lib.logsettings import get_logger_config
from util.config_parse import convert_tokens
import os

from path import Path as path
from xmodule.modulestore.modulestore_settings import convert_module_store_setting_if_needed

# https://stackoverflow.com/questions/2890146/how-to-force-pyyaml-to-load-strings-as-unicode-objects
from yaml import Loader, SafeLoader


def construct_yaml_str(self, node):
    """
    Override the default string handling function
    to always return unicode objects
    """
    return self.construct_scalar(node)
Loader.add_constructor(u'tag:yaml.org,2002:str', construct_yaml_str)
SafeLoader.add_constructor(u'tag:yaml.org,2002:str', construct_yaml_str)

# SERVICE_VARIANT specifies name of the variant used, which decides what YAML
# configuration files are read during startup.
SERVICE_VARIANT = os.environ.get('SERVICE_VARIANT', None)

# CONFIG_ROOT specifies the directory where the YAML configuration
# files are expected to be found. If not specified, use the project
# directory.
CONFIG_ROOT = path(os.environ.get('CONFIG_ROOT', ENV_ROOT))

# CONFIG_PREFIX specifies the prefix of the YAML configuration files,
# based on the service variant. If no variant is use, don't use a
# prefix.
CONFIG_PREFIX = SERVICE_VARIANT + "." if SERVICE_VARIANT else ""

##############################################################
#
# DEFAULT SETTINGS FOR PRODUCTION
#
# These are defaults common for all production deployments
#

DEBUG = False
TEMPLATE_DEBUG = False

EMAIL_BACKEND = 'django_ses.SESBackend'
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

GIT_REPO_EXPORT_DIR = '/edx/var/edxapp/export_course_repos'
SESSION_INACTIVITY_TIMEOUT_IN_SECONDS = None
EMAIL_FILE_PATH = None
STATIC_URL_BASE = None
STATIC_ROOT_BASE = None
SESSION_COOKIE_NAME = None
ADDL_INSTALLED_APPS = []
AUTH_USE_CAS = False
CAS_ATTRIBUTE_CALLBACK = None
MICROSITE_ROOT_DIR = ''
CMS_SEGMENT_KEY = None
DATADOG = {}
ADDL_INSTALLED_APPS = []
LOCAL_LOGLEVEL = 'INFO'
##############################################################
#
# ENV TOKEN IMPORT
#
# Currently non-secure and secure settings are managed
# in two yaml files. This section imports the non-secure
# settings and modifies them in code if necessary.
#

with open(CONFIG_ROOT / CONFIG_PREFIX + "env.yaml") as env_file:
    ENV_TOKENS = yaml.safe_load(env_file)

ENV_TOKENS = convert_tokens(ENV_TOKENS)

##############################################################
#
# DEFAULT SETTINGS FOR CELERY
#

# Don't use a connection pool, since connections are dropped by ELB.
BROKER_POOL_LIMIT = 0
BROKER_CONNECTION_TIMEOUT = 1

# For the Result Store, use the django cache named 'celery'
CELERY_RESULT_BACKEND = 'djcelery.backends.cache:CacheBackend'

# When the broker is behind an ELB, use a heartbeat to refresh the
# connection and to detect if it has been dropped.
BROKER_HEARTBEAT = 10.0
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

ENV_CELERY_QUEUES = ENV_TOKENS.get('CELERY_QUEUES', None)
if ENV_CELERY_QUEUES:
    CELERY_QUEUES = {queue: {} for queue in ENV_CELERY_QUEUES}
else:
    CELERY_QUEUES = {
        HIGH_PRIORITY_QUEUE: {},
        LOW_PRIORITY_QUEUE: {},
        DEFAULT_PRIORITY_QUEUE: {}
    }

CELERY_ALWAYS_EAGER = False

##########################################
# Merge settings from common.py
#
# Before the tokens are imported directly
# into settings some dictionary settings
# need to be merged from common.py

ENV_FEATURES = ENV_TOKENS.get('FEATURES', {})
for feature, value in ENV_FEATURES.items():
    FEATURES[feature] = value

# Delete keys from ENV_TOKENS so that when it's imported
# into settings it doesn't override what was set above
if 'FEATURES' in ENV_TOKENS:
    del ENV_TOKENS['FEATURES']

vars().update(ENV_TOKENS)

##########################################
# Manipulate imported settings with code
#
# For historical reasons some settings need
# to be modified in code.  For example
# conversions to other data structures that
# cannot be represented in YAML.

if STATIC_URL_BASE:
    # collectstatic will fail if STATIC_URL is a unicode string
    STATIC_URL = STATIC_URL_BASE.encode('ascii')
    if not STATIC_URL.endswith("/"):
        STATIC_URL += "/"
    STATIC_URL += EDX_PLATFORM_REVISION + "/"

if STATIC_ROOT_BASE:
    STATIC_ROOT = path(STATIC_ROOT_BASE) / EDX_PLATFORM_REVISION


# Cache used for location mapping -- called many times with the same key/value
# in a given request.
if 'loc_cache' not in CACHES:
    CACHES['loc_cache'] = {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'edx_location_mem_cache',
    }


# allow for environments to specify what cookie name our login subsystem should use
# this is to fix a bug regarding simultaneous logins between edx.org and edge.edx.org which can
# happen with some browsers (e.g. Firefox)
if SESSION_COOKIE_NAME:
    # NOTE, there's a bug in Django (http://bugs.python.org/issue18012) which necessitates this being a str()
    SESSION_COOKIE_NAME = str(SESSION_COOKIE_NAME)


# Additional installed apps
for app in ADDL_INSTALLED_APPS:
    INSTALLED_APPS += (app,)


LOGGING = get_logger_config(LOG_DIR,
                            local_loglevel=LOCAL_LOGLEVEL,
                            logging_env=LOGGING_ENV,
                            debug=False,
                            service_variant=SERVICE_VARIANT)

if AUTH_USE_CAS:
    AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend',
        'django_cas.backends.CASBackend',
    )
    INSTALLED_APPS += ('django_cas',)
    MIDDLEWARE_CLASSES += ('django_cas.middleware.CASMiddleware',)
    if CAS_ATTRIBUTE_CALLBACK:
        import importlib
        CAS_USER_DETAILS_RESOLVER = getattr(
            importlib.import_module(CAS_ATTRIBUTE_CALLBACK['module']),
            CAS_ATTRIBUTE_CALLBACK['function']
        )

MICROSITE_ROOT_DIR = path(MICROSITE_ROOT_DIR)

##############################################################
#
# AUTH TOKEN IMPORT
#

with open(CONFIG_ROOT / CONFIG_PREFIX + "auth.yaml") as auth_file:
    AUTH_TOKENS = yaml.safe_load(auth_file)

AUTH_TOKENS = convert_tokens(AUTH_TOKENS)

vars().update(AUTH_TOKENS)

##########################################
# Manipulate imported settings with code
#

if AWS_ACCESS_KEY_ID == "":
    AWS_ACCESS_KEY_ID = None

if AWS_SECRET_ACCESS_KEY == "":
    AWS_SECRET_ACCESS_KEY = None

MODULESTORE = convert_module_store_setting_if_needed(MODULESTORE)

# TODO: deprecated (compatibility with previous settings)
if 'DATADOG_API' in AUTH_TOKENS:
    DATADOG['api_key'] = AUTH_TOKENS['DATADOG_API']

BROKER_URL = "{0}://{1}:{2}@{3}/{4}".format(CELERY_BROKER_TRANSPORT,
                                            CELERY_BROKER_USER,
                                            CELERY_BROKER_PASSWORD,
                                            CELERY_BROKER_HOSTNAME,
                                            CELERY_BROKER_VHOST)

######################## CUSTOM COURSES for EDX CONNECTOR ######################
if FEATURES.get('CUSTOM_COURSES_EDX'):
    INSTALLED_APPS += ('openedx.core.djangoapps.ccxcon',)
