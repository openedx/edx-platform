
# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=W0401, W0614

from ..dev import *

CLASSES_TO_DBS = {
    'BerkeleyX/CS169.1x/2012_Fall': "cs169.db",
    'BerkeleyX/CS188.1x/2012_Fall': "cs188_1.db",
    'HarvardX/CS50x/2012': "cs50.db",
    'HarvardX/PH207x/2012_Fall': "ph207.db",
    'edX/3.091x/2012_Fall': "3091.db",
    'edX/6.002x/2012_Fall': "6002.db",
    'edX/6.00x/2012_Fall': "600.db",
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
       'KEY_PREFIX': 'general',
       'VERSION': 5,
       'KEY_FUNCTION': 'util.memcache.safe_key',
   }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'


def path_for_db(db_name):
    return ENV_ROOT / "db" / db_name


def course_db_for(course_id):
    db_name = CLASSES_TO_DBS[course_id]
    return {
               'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': path_for_db(db_name)
                }
            }
