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

BOOK_URL = ENV_TOKENS['BOOK_URL'] # 'https://mitxstatic.s3.amazonaws.com/book_images/'
LIB_URL = ENV_TOKENS['LIB_URL'] # 'https://mitxstatic.s3.amazonaws.com/js/'
MEDIA_URL = ENV_TOKENS['MEDIA_URL'] # 'http://s3.amazonaws.com/mitx_askbot_stage/'

LOG_DIR = ENV_TOKENS['LOG_DIR'] # "/mnt/logs/"

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
    }
}

CACHES = {
   'default': {
       'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
       'LOCATION': '127.0.0.1:11211',
   },
   'general': {
       'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
       'LOCATION': '127.0.0.1:11211',
       'KEY_PREFIX' : 'general',
       'VERSION' : 5,
   }
}

############################## SECURE AUTH ITEMS ###############################
# Secret things: passwords, access keys, etc.
with open(BASE_DIR / "auth.json") as auth_file:
    AUTH_TOKENS = json.load(auth_file)

AWS_ACCESS_KEY_ID = AUTH_TOKENS["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = AUTH_TOKENS["AWS_SECRET_ACCESS_KEY"]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'wwc',
        'USER': 'root',
        'PASSWORD': authtokens["PASSWORD"],
        'HOST': 'staging.ciqreuddjk02.us-east-1.rds.amazonaws.com',
        'PORT': '3306',
    }
}