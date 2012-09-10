"""
This is the default template for our main set of AWS servers. This does NOT
cover the content machines, which use content.py

Common traits:
* Use memcached, and cache-backed sessions
* Use a MySQL 5.1 database
"""
import json

from .logsettings import get_logger_config
from .common import *

############################### ALWAYS THE SAME ################################
DEBUG = False
TEMPLATE_DEBUG = False

EMAIL_BACKEND = 'django_ses.SESBackend'
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

# Disable askbot, enable Berkeley forums
MITX_FEATURES['ENABLE_DISCUSSION'] = False
MITX_FEATURES['ENABLE_DISCUSSION_SERVICE'] = True

# IMPORTANT: With this enabled, the server must always be behind a proxy that 
# strips the header HTTP_X_FORWARDED_PROTO from client requests. Otherwise,
# a user can fool our server into thinking it was an https connection.
# See https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
# for other warnings.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

########################### NON-SECURE ENV CONFIG ##############################
# Things like server locations, ports, etc.

with open(ENV_ROOT / "env.json") as env_file:
    ENV_TOKENS = json.load(env_file)

SITE_NAME = ENV_TOKENS['SITE_NAME']

BOOK_URL = ENV_TOKENS['BOOK_URL']
MEDIA_URL = ENV_TOKENS['MEDIA_URL']
LOG_DIR = ENV_TOKENS['LOG_DIR']

CACHES = ENV_TOKENS['CACHES']

for feature, value in ENV_TOKENS.get('MITX_FEATURES', {}).items():
    MITX_FEATURES[feature] = value

WIKI_ENABLED = ENV_TOKENS.get('WIKI_ENABLED', WIKI_ENABLED)
local_loglevel = ENV_TOKENS.get('LOCAL_LOGLEVEL', 'INFO')

LOGGING = get_logger_config(LOG_DIR,
                            logging_env=ENV_TOKENS['LOGGING_ENV'],
                            syslog_addr=(ENV_TOKENS['SYSLOG_SERVER'], 514),
                            local_loglevel=local_loglevel,
                            debug=False)

COURSE_LISTINGS = ENV_TOKENS.get('COURSE_LISTINGS', {})
SUBDOMAIN_BRANDING = ENV_TOKENS.get('SUBDOMAIN_BRANDING', {})
COMMENTS_SERVICE_URL = ENV_TOKENS.get("COMMENTS_SERVICE_URL",'')
COMMENTS_SERVICE_KEY = ENV_TOKENS.get("COMMENTS_SERVICE_KEY",'')

############################## SECURE AUTH ITEMS ###############################
# Secret things: passwords, access keys, etc.
with open(ENV_ROOT / "auth.json") as auth_file:
    AUTH_TOKENS = json.load(auth_file)

SECRET_KEY = AUTH_TOKENS['SECRET_KEY']

AWS_ACCESS_KEY_ID = AUTH_TOKENS["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = AUTH_TOKENS["AWS_SECRET_ACCESS_KEY"]

DATABASES = AUTH_TOKENS['DATABASES']

XQUEUE_INTERFACE = AUTH_TOKENS['XQUEUE_INTERFACE']

if 'COURSE_ID' in ENV_TOKENS:
    ASKBOT_URL = "courses/{0}/discussions/".format(ENV_TOKENS['COURSE_ID'])

