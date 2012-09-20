"""
This is the default template for our main set of AWS servers.
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

########################### NON-SECURE ENV CONFIG ##############################
# Things like server locations, ports, etc.
with open(ENV_ROOT / "cms.env.json") as env_file:
    ENV_TOKENS = json.load(env_file)

LMS_BASE = ENV_TOKENS.get('LMS_BASE')

SITE_NAME = ENV_TOKENS['SITE_NAME']

LOG_DIR = ENV_TOKENS['LOG_DIR']

CACHES = ENV_TOKENS['CACHES']

for feature, value in ENV_TOKENS.get('MITX_FEATURES', {}).items():
    MITX_FEATURES[feature] = value

LOGGING = get_logger_config(LOG_DIR,
                            logging_env=ENV_TOKENS['LOGGING_ENV'],
                            syslog_addr=(ENV_TOKENS['SYSLOG_SERVER'], 514),
                            debug=False)

with open(ENV_ROOT / "repos.json") as repos_file:
    REPOS = json.load(repos_file)


############################## SECURE AUTH ITEMS ###############################
# Secret things: passwords, access keys, etc.
with open(ENV_ROOT / "cms.auth.json") as auth_file:
    AUTH_TOKENS = json.load(auth_file)

AWS_ACCESS_KEY_ID = AUTH_TOKENS["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = AUTH_TOKENS["AWS_SECRET_ACCESS_KEY"]
DATABASES = AUTH_TOKENS['DATABASES']
MODULESTORE = AUTH_TOKENS['MODULESTORE']
