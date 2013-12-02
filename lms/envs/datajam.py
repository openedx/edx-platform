"""
Specific overrides to the base prod settings to make development easier.
"""

from .aws import * # pylint: disable=wildcard-import, unused-wildcard-import

DEBUG = True
USE_I18N = True
TEMPLATE_DEBUG = True

# By default don't use a worker, execute tasks as if they were local functions
CELERY_ALWAYS_EAGER = True

################################ LOGGERS ######################################

import logging

# Disable noisy loggers
for pkg_name in ['track.contexts', 'track.middleware', 'dd.dogapi']:
    logging.getLogger(pkg_name).setLevel(logging.CRITICAL)


################################ EMAIL ########################################

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
MITX_FEATURES['ENABLE_INSTRUCTOR_EMAIL'] = True     # Enable email for all Studio courses
MITX_FEATURES['REQUIRE_COURSE_EMAIL_AUTH'] = False  # Give all courses email (don't require django-admin perms)


################################ DEBUG TOOLBAR ################################

INSTALLED_APPS += ('debug_toolbar',)
MIDDLEWARE_CLASSES += ('django_comment_client.utils.QueryCountDebugMiddleware',
                       'debug_toolbar.middleware.DebugToolbarMiddleware',)
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
)

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False
}

########################### PIPELINE #################################

PIPELINE_SASS_ARGUMENTS = '--debug-info --require {proj_dir}/static/sass/bourbon/lib/bourbon.rb'.format(proj_dir=PROJECT_ROOT)

########################### INSIGHTS #################################

# set up tracking logs to output to the Insights server:
TRACKING_BACKENDS.update({
    'insights': {
        'ENGINE': 'track.backends.logger.LoggerBackend',
        'OPTIONS': {
            'name': 'sendevent'
        }
    }
})

from logging.handlers import HTTPHandler
logger=logging.getLogger('sendevent')
logger.addHandler(HTTPHandler("localhost:8002", "/httpevent"))

# Set up analytics requests from the instructor dash to also
# go to Insights.  (Note that analytics requests add
#    "get?aname={}&course_id={}&apikey={}"
# to the URL.

ANALYTICS_SERVER_URL = "http://localhost:8002/query/analytics_"

#####################################################################
# Lastly, see if the developer has any local overrides.
try:
    from .private import *      # pylint: disable=F0401
except ImportError:
    pass
