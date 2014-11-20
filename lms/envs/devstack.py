"""
Specific overrides to the base prod settings to make development easier.
"""

from .aws import *  # pylint: disable=wildcard-import, unused-wildcard-import

# Don't use S3 in devstack, fall back to filesystem
del DEFAULT_FILE_STORAGE
MEDIA_ROOT = "/edx/var/edxapp/uploads"


DEBUG = True
USE_I18N = True
TEMPLATE_DEBUG = True
SITE_NAME = 'localhost:8000'
# By default don't use a worker, execute tasks as if they were local functions
CELERY_ALWAYS_EAGER = True

################################ LOGGERS ######################################

import logging

# Disable noisy loggers
for pkg_name in ['track.contexts', 'track.middleware', 'dd.dogapi']:
    logging.getLogger(pkg_name).setLevel(logging.CRITICAL)


################################ EMAIL ########################################

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
FEATURES['ENABLE_INSTRUCTOR_EMAIL'] = True     # Enable email for all Studio courses
FEATURES['REQUIRE_COURSE_EMAIL_AUTH'] = False  # Give all courses email (don't require django-admin perms)


########################## ANALYTICS TESTING ########################

ANALYTICS_SERVER_URL = "http://127.0.0.1:9000/"
ANALYTICS_API_KEY = ""

# Set this to the dashboard URL in order to display the link from the
# dashboard to the Analytics Dashboard.
ANALYTICS_DASHBOARD_URL = None


################################ DEBUG TOOLBAR ################################

INSTALLED_APPS += ('debug_toolbar', 'debug_toolbar_mongo')
MIDDLEWARE_CLASSES += ('django_comment_client.utils.QueryCountDebugMiddleware',
                       'debug_toolbar.middleware.DebugToolbarMiddleware',)
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
    'debug_toolbar_mongo.panel.MongoDebugPanel',
    'debug_toolbar.panels.profiling.ProfilingPanel',
)

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': 'lms.envs.devstack.should_show_debug_toolbar'
}

should_show_debug_toolbar = lambda _: True  # We always want the toolbar on devstack regardless of IP, auth, etc.

########################### PIPELINE #################################

PIPELINE_SASS_ARGUMENTS = '--debug-info --require {proj_dir}/static/sass/bourbon/lib/bourbon.rb'.format(proj_dir=PROJECT_ROOT)

########################### VERIFIED CERTIFICATES #################################

FEATURES['AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING'] = True
FEATURES['ENABLE_PAYMENT_FAKE'] = True

CC_PROCESSOR_NAME = 'CyberSource2'
CC_PROCESSOR = {
    'CyberSource2': {
        "PURCHASE_ENDPOINT": '/shoppingcart/payment_fake/',
        "SECRET_KEY": 'abcd123',
        "ACCESS_KEY": 'abcd123',
        "PROFILE_ID": 'edx',
    }
}

########################### External REST APIs #################################
FEATURES['ENABLE_MOBILE_REST_API'] = True
FEATURES['ENABLE_VIDEO_ABSTRACTION_LAYER_API'] = True

#####################################################################
# See if the developer has any local overrides.
try:
    from .private import *      # pylint: disable=F0401
except ImportError:
    pass

#####################################################################
# Lastly, run any migrations, if needed.
MODULESTORE = convert_module_store_setting_if_needed(MODULESTORE)
