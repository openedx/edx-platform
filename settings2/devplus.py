"""
This config file tries to mimic the production environment more closely than the
normal dev.py. It assumes you're running a local instance of MySQL 5.1 and that
you're running memcached.
"""
from common import *

CSRF_COOKIE_DOMAIN = 'localhost'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'wwc',  # Or path to database file if using sqlite3.
        'USER': 'root', # Not used with sqlite3.
        'PASSWORD': '', # Not used with sqlite3.
        'HOST': '127.0.0.1', # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '3306',      # Set to empty string for default. Not used with sqlite3.
    }
}

# Make this unique, and don't share it with anybody.
SECRET_KEY = '85920908f28904ed733fe576320db18cabd7b6cd'

CACHES = {
   'default': {
       'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
       'LOCATION': '127.0.0.1:11211',
   }
}


SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

DEBUG = True
TEMPLATE_DEBUG = True