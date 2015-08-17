"""
This config file tries to mimic the production environment more closely than the
normal dev.py. It assumes you're running a local instance of MySQL 5.1 and that
you're running memcached. You'll want to use this to test caching and database
migrations.

Assumptions:
* MySQL 5.1 (version important?  (askbot breaks on 5.5, but that's gone now))

Dir structure:
/envroot/
        /edx-platform # The location of this repo
        /log  # Where we're going to write log files

"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=wildcard-import, unused-wildcard-import

from .dev import *

WIKI_ENABLED = True

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
        'KEY_PREFIX': 'general',
        'VERSION': 5,
        'KEY_FUNCTION': 'util.memcache.safe_key',
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'


################################ DEBUG TOOLBAR #################################
INSTALLED_APPS += ('debug_toolbar',)
MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
INTERNAL_IPS = ('127.0.0.1',)

DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.profiling.ProfilingPanel',
)

#PIPELINE = True
