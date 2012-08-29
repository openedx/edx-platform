"""
This config file runs the simplest dev environment using sqlite, and db-based
sessions. Assumes structure:

/envroot/
        /db   # This is where it'll write the database file
        /mitx # The location of this repo
        /log  # Where we're going to write log files
"""
from .common import *
from .logsettings import get_logger_config

DEBUG = True
TEMPLATE_DEBUG = True

MITX_FEATURES['DISABLE_START_DATES'] = True
MITX_FEATURES['ENABLE_SQL_TRACKING_LOGS'] = True
MITX_FEATURES['SUBDOMAIN_COURSE_LISTINGS'] = False  # Enable to test subdomains--otherwise, want all courses to show up
MITX_FEATURES['SUBDOMAIN_BRANDING'] = True

WIKI_ENABLED = True

LOGGING = get_logger_config(ENV_ROOT / "log",
                            logging_env="dev",
                            tracking_filename="tracking.log",
                            debug=True)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ENV_ROOT / "db" / "mitx.db",
    }
}

CACHES = {
    # This is the cache used for most things. Askbot will not work without a
    # functioning cache -- it relies on caching to load its settings in places.
    # In staging/prod envs, the sessions also live here.
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'mitx_loc_mem_cache',
        'KEY_FUNCTION': 'util.memcache.safe_key',
    },

    # The general cache is what you get if you use our util.cache. It's used for
    # things like caching the course.xml file for different A/B test groups.
    # We set it to be a DummyCache to force reloading of course.xml in dev.
    # In staging environments, we would grab VERSION from data uploaded by the
    # push process.
    'general': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        'KEY_PREFIX': 'general',
        'VERSION': 4,
        'KEY_FUNCTION': 'util.memcache.safe_key',
    }
}

XQUEUE_INTERFACE = {
    "url": "https://sandbox-xqueue.edx.org",
    "django_auth": {
        "username": "lms",
        "password": "***REMOVED***"
    },
    "basic_auth": ('anant', 'agarwal'),
}

# Make the keyedcache startup warnings go away
CACHE_TIMEOUT = 0

# Dummy secret key for dev
SECRET_KEY = '85920908f28904ed733fe576320db18cabd7b6cd'

COURSE_LISTINGS = {
    'default': ['BerkeleyX/CS169.1x/2012_Fall',
                'BerkeleyX/CS188.1x/2012_Fall',
                'HarvardX/CS50x/2012',
                'HarvardX/PH207x/2012_Fall',
                'MITx/3.091x/2012_Fall',
                'MITx/6.002x/2012_Fall',
                'MITx/6.00x/2012_Fall'],
    'berkeley': ['BerkeleyX/CS169.1x/Cal_2012_Fall',
                 'BerkeleyX/CS188.1x/Cal_2012_Fall'],
    'harvard': ['HarvardX/CS50x/2012H'],
    'mit': [],
    'sjsu': ['MITx/6.002x-EE98/2012_Fall_SJSU'],
}

SUBDOMAIN_BRANDING = {
    'sjsu': 'MITx',
    'mit': 'MITx',
    'berkeley': 'BerkeleyX',
    'harvard': 'HarvardX',
}

COMMENTS_SERVICE_KEY = "PUT_YOUR_API_KEY_HERE"

################################ LMS Migration #################################
MITX_FEATURES['ENABLE_LMS_MIGRATION'] = True
MITX_FEATURES['ACCESS_REQUIRE_STAFF_FOR_COURSE'] = False   # require that user be in the staff_* group to be able to enroll
MITX_FEATURES['USE_XQA_SERVER'] = 'http://xqa:server@content-qa.mitx.mit.edu/xqa'

INSTALLED_APPS += ('lms_migration',)

LMS_MIGRATION_ALLOWED_IPS = ['127.0.0.1']

################################ OpenID Auth #################################
MITX_FEATURES['AUTH_USE_OPENID'] = True
MITX_FEATURES['AUTH_USE_OPENID_PROVIDER'] = True
MITX_FEATURES['BYPASS_ACTIVATION_EMAIL_FOR_EXTAUTH'] = True

INSTALLED_APPS += ('external_auth',)
INSTALLED_APPS += ('django_openid_auth',)

OPENID_CREATE_USERS = False
OPENID_UPDATE_DETAILS_FROM_SREG = True
OPENID_SSO_SERVER_URL = 'https://www.google.com/accounts/o8/id'	# TODO: accept more endpoints
OPENID_USE_AS_ADMIN_LOGIN = False

OPENID_PROVIDER_TRUSTED_ROOTS = ['*'] 

################################ MIT Certificates SSL Auth #################################
MITX_FEATURES['AUTH_USE_MIT_CERTIFICATES'] = True

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
#  'debug_toolbar.panels.profiling.ProfilingDebugPanel',
)

############################ FILE UPLOADS (ASKBOT) #############################
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_ROOT = ENV_ROOT / "uploads"
MEDIA_URL = "/static/uploads/"
STATICFILES_DIRS.append(("uploads", MEDIA_ROOT))
FILE_UPLOAD_TEMP_DIR = ENV_ROOT / "uploads"
FILE_UPLOAD_HANDLERS = (
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
)

########################### PIPELINE #################################

PIPELINE_SASS_ARGUMENTS = '-r {proj_dir}/static/sass/bourbon/lib/bourbon.rb'.format(proj_dir=PROJECT_ROOT)
