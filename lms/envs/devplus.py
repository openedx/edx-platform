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
# pylint: disable=W0401, W0614

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
   'debug_toolbar.panels.version.VersionDebugPanel',
   'debug_toolbar.panels.timer.TimerDebugPanel',
   'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
   'debug_toolbar.panels.headers.HeaderDebugPanel',
   'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
   'debug_toolbar.panels.sql.SQLDebugPanel',
   'debug_toolbar.panels.signals.SignalDebugPanel',
   'debug_toolbar.panels.logger.LoggingPanel',

#  Enabling the profiler has a weird bug as of django-debug-toolbar==0.9.4 and
#  Django=1.3.1/1.4 where requests to views get duplicated (your method gets
#  hit twice). So you can uncomment when you need to diagnose performance
#  problems, but you shouldn't leave it on.
  'debug_toolbar.panels.profiling.ProfilingDebugPanel',
)

#PIPELINE_ENABLED = True
