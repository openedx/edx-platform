"""
This config file runs the simplest dev environment using sqlite, and db-based
sessions. Assumes structure:

/envroot/
        /db   # This is where it'll write the database file
        /mitx # The location of this repo

"""
from common import *

CSRF_COOKIE_DOMAIN = 'localhost'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ENV_ROOT / "db" / "mitx.db",
    }
}

# Make this unique, and don't share it with anybody.
SECRET_KEY = '85920908f28904ed733fe576320db18cabd7b6cd'

DEBUG = True
TEMPLATE_DEBUG = True

# This is disabling ASKBOT, but not properly overwriting INSTALLED_APPS. ???
# It's because our ASKBOT_ENABLED here is actually shadowing the real one.
# 
# ASKBOT_ENABLED = True
# MITX_FEATURES['SAMPLE'] = True  # Switch to this system so we get around the shadowing

INSTALLED_APPS = installed_apps(extras=['debug_toolbar'])
MIDDLEWARE_CLASSES = ('debug_toolbar.middleware.DebugToolbarMiddleware',) + MIDDLEWARE_CLASSES

DEBUG_TOOLBAR_PANELS = (
   'debug_toolbar.panels.version.VersionDebugPanel',
   'debug_toolbar.panels.timer.TimerDebugPanel',
#  'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
   'debug_toolbar.panels.headers.HeaderDebugPanel',
   'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
   'debug_toolbar.panels.sql.SQLDebugPanel',
   'debug_toolbar.panels.signals.SignalDebugPanel',
   'debug_toolbar.panels.logger.LoggingPanel',
#   'debug_toolbar.panels.profiling.ProfilingDebugPanel', # Lots of overhead
)
