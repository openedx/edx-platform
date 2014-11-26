"""
This is the default template for our main set of AWS servers. This does NOT
cover the content machines, which use content.py

Common traits:
* Use memcached, and cache-backed sessions
* Use a MySQL 5.1 database
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=W0401, W0614

import json
import yaml
from pprint import pprint 

from .common import *
from logsettings import get_logger_config
import os

from path import path
from xmodule.modulestore.modulestore_settings import convert_module_store_setting_if_needed

# https://stackoverflow.com/questions/2890146/how-to-force-pyyaml-to-load-strings-as-unicode-objects
from yaml import Loader, SafeLoader
def construct_yaml_str(self, node):
    # Override the default string handling function 
    # to always return unicode objects
    return self.construct_scalar(node)
Loader.add_constructor(u'tag:yaml.org,2002:str', construct_yaml_str)
SafeLoader.add_constructor(u'tag:yaml.org,2002:str', construct_yaml_str)

def convert_tokens(tokens):
   
    for k, v in tokens.iteritems():
        if v == 'None':
            tokens[k] = None
         
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


####################### START ENV_TOKENS #######################

with open(CONFIG_ROOT / CONFIG_PREFIX + "env.yaml") as env_file:
    ENV_TOKENS = yaml.load(env_file)

convert_tokens(ENV_TOKENS)

# These settings are merged from common.py
ENV_FEATURES = ENV_TOKENS.get('FEATURES', ENV_TOKENS.get('MITX_FEATURES', {}))
for feature, value in ENV_FEATURES.items():
    FEATURES[feature] = value

MKTG_URL_LINK_MAP.update(ENV_TOKENS.get('MKTG_URL_LINK_MAP', {}))

if 'FEATURES' in ENV_TOKENS:
	del ENV_TOKENS['FEATURES']

if 'MKTG_URL_LINK_MAP' in ENV_TOKENS:
	del ENV_TOKENS['MKTG_URL_LINK_MAP']

vars().update(ENV_TOKENS)

if SESSION_COOKIE_NAME:
    # NOTE, there's a bug in Django (http://bugs.python.org/issue18012) which necessitates this being a str()
    SESSION_COOKIE_NAME = str(SESSION_COOKIE_NAME)

MICROSITE_ROOT_DIR = path(MICROSITE_ROOT_DIR)

# Cache used for location mapping -- called many times with the same key/value
# in a given request.
if 'loc_cache' not in CACHES:
    CACHES['loc_cache'] = {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'edx_location_mem_cache',
    }

# We want Bulk Email running on the high-priority queue, so we define the
# routing key that points to it.  At the moment, the name is the same.
# We have to reset the value here, since we have changed the value of the queue name.
BULK_EMAIL_ROUTING_KEY = HIGH_PRIORITY_QUEUE

LANGUAGE_DICT = dict(LANGUAGES)

# Additional installed apps
for app in ENV_TOKENS.get('ADDL_INSTALLED_APPS', []):
    INSTALLED_APPS += (app,)

local_loglevel = ENV_TOKENS.get('LOCAL_LOGLEVEL', 'INFO')

LOGGING = get_logger_config(LOG_DIR,
                            logging_env=LOGGING_ENV,
                            local_loglevel=local_loglevel,
                            debug=False,
                            service_variant=SERVICE_VARIANT)

for name, value in ENV_TOKENS.get("CODE_JAIL", {}).items():
    oldvalue = CODE_JAIL.get(name)
    if isinstance(oldvalue, dict):
        for subname, subvalue in value.items():
            oldvalue[subname] = subvalue
    else:
        CODE_JAIL[name] = value


if FEATURES.get('AUTH_USE_CAS'):
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


STATIC_ROOT = path(STATIC_ROOT_BASE)

####################### END ENV_TOKENS #######################


with open(CONFIG_ROOT / CONFIG_PREFIX + "auth.yaml") as auth_file:
    AUTH_TOKENS = yaml.load(auth_file)

convert_tokens(AUTH_TOKENS)

vars().update(AUTH_TOKENS)

FEATURES['SEGMENT_IO_LMS'] = SEGMENT_IO_LMS

if AWS_ACCESS_KEY_ID == "":
    AWS_ACCESS_KEY_ID = None

if AWS_SECRET_ACCESS_KEY == "":
    AWS_SECRET_ACCESS_KEY = None

# TODO: deprecated (compatibility with previous settings)
if 'DATADOG_API' in AUTH_TOKENS:
    DATADOG['api_key'] = AUTH_TOKENS['DATADOG_API']

BROKER_URL = "{0}://{1}:{2}@{3}/{4}".format(CELERY_BROKER_TRANSPORT,
                                            CELERY_BROKER_USER,
                                            CELERY_BROKER_PASSWORD,
                                            CELERY_BROKER_HOSTNAME,
                                            CELERY_BROKER_VHOST)

# Grades download
GRADES_DOWNLOAD_ROUTING_KEY = HIGH_MEM_QUEUE
