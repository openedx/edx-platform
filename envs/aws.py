"""
This is the default template for our main set of AWS servers. This does NOT
cover the content machines, which use content.py

Common traits:
* Use memcached, and cache-backed sessions
* Use a MySQL 5.1 database
"""
import json

from common import *

############################### ALWAYS THE SAME ################################
DEBUG = False
TEMPLATE_DEBUG = False

EMAIL_BACKEND = 'django_ses.SESBackend'
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

########################### NON-SECURE ENV CONFIG ##############################
# Things like server locations, ports, etc.
with open(BASE_DIR / "env.json") as env_file:
    ENV_TOKENS = json.load(env_file)

SITE_NAME = ENV_TOKENS['SITE_NAME'] # "extstage.mitx.mit.edu"
CSRF_COOKIE_DOMAIN = ENV_TOKENS['CSRF_COOKIE_DOMAIN'] # '.mitx.mit.edu'

BOOK_URL = ENV_TOKENS['BOOK_URL']
LIB_URL = ENV_TOKENS['LIB_URL']
MEDIA_URL = ENV_TOKENS['MEDIA_URL']
LOG_DIR = ENV_TOKENS['LOG_DIR']

CACHES = ENV_TOKENS['CACHES']

############################## SECURE AUTH ITEMS ###############################
# Secret things: passwords, access keys, etc.
with open(BASE_DIR / "auth.json") as auth_file:
    AUTH_TOKENS = json.load(auth_file)

SECRET_KEY = AUTH_TOKENS['SECRET_KEY']

AWS_ACCESS_KEY_ID = AUTH_TOKENS["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = AUTH_TOKENS["AWS_SECRET_ACCESS_KEY"]

DATABASES = AUTH_TOKENS['DATABASES']