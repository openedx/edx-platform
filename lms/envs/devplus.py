"""
This config file tries to mimic the production environment more closely than the
normal dev.py. It assumes you're running a local instance of MySQL 5.1 and that
you're running memcached. You'll want to use this to test caching and database
migrations.

Assumptions:
* MySQL 5.1 (version important -- askbot breaks on 5.5)

Dir structure:
/envroot/
        /mitx # The location of this repo
        /log  # Where we're going to write log files

"""
from .dev import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'wwc',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}

CACHES = {
   'default': {
       'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
       'LOCATION': '127.0.0.1:11211',
       'KEY_FUNCTION': 'util.memcache.safe_key',
   },
   'general': {
       'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
       'LOCATION': '127.0.0.1:11211',
       'KEY_PREFIX' : 'general',
       'VERSION' : 5,
       'KEY_FUNCTION': 'util.memcache.safe_key',
   }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
