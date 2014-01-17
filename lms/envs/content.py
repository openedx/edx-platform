"""
These are debug machines used for content creators, so they're kind of a cross
between dev machines and AWS machines.
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=W0401, W0614

from .aws import *

DEBUG = True
TEMPLATE_DEBUG = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

################################ DEBUG TOOLBAR #################################
INSTALLED_APPS += ('debug_toolbar',)
MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)

DEBUG_TOOLBAR_PANELS = (
   'debug_toolbar.panels.versions.VersionsPanel',
   'debug_toolbar.panels.timer.TimerPanel',
   'debug_toolbar.panels.settings.SettingsPanel',
   'debug_toolbar.panels.headers.HeadersPanel',
   'debug_toolbar.panels.request.RequestPanel',
   'debug_toolbar.panels.sql.SQLPanel',
   'debug_toolbar.panels.signals.SignalsPanel',
   'debug_toolbar.panels.logging.LoggingPanel',


#  Enabling the profiler has a weird bug as of django-debug-toolbar==0.9.4 and
#  Django=1.3.1/1.4 where requests to views get duplicated (your method gets
#  hit twice). So you can uncomment when you need to diagnose performance
#  problems, but you shouldn't leave it on.
#  'debug_toolbar.panels.profiling.ProfilingDebugPanel',
)
