"""
This config file runs the simplest dev environment using sqlite, and db-based
sessions. Assumes structure:

/envroot/
        /db   # This is where it'll write the database file
        /edx-platform  # The location of this repo
        /log  # Where we're going to write log files
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=wildcard-import, unused-wildcard-import

from openedx.stanford.lms.envs.common import *

DEBUG = True
TEMPLATE_DEBUG = True

HTTPS = 'off'
FEATURES['DISABLE_START_DATES'] = False
FEATURES['ENABLE_SQL_TRACKING_LOGS'] = True
FEATURES['SUBDOMAIN_COURSE_LISTINGS'] = False  # Enable to test subdomains--otherwise, want all courses to show up
FEATURES['SUBDOMAIN_BRANDING'] = True
FEATURES['FORCE_UNIVERSITY_DOMAIN'] = None		# show all university courses if in dev (ie don't use HTTP_HOST)
FEATURES['ENABLE_MANUAL_GIT_RELOAD'] = True
FEATURES['ENABLE_PSYCHOMETRICS'] = False    # real-time psychometrics (eg item response theory analysis in instructor dashboard)
FEATURES['ENABLE_SERVICE_STATUS'] = True
FEATURES['ENABLE_INSTRUCTOR_EMAIL'] = True     # Enable email for all Studio courses
FEATURES['REQUIRE_COURSE_EMAIL_AUTH'] = False  # Give all courses email (don't require django-admin perms)
FEATURES['ENABLE_HINTER_INSTRUCTOR_VIEW'] = True
FEATURES['ENABLE_INSTRUCTOR_LEGACY_DASHBOARD'] = True
FEATURES['MULTIPLE_ENROLLMENT_ROLES'] = True
FEATURES['ENABLE_SHOPPING_CART'] = True
FEATURES['AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING'] = True
FEATURES['ENABLE_S3_GRADE_DOWNLOADS'] = True
FEATURES['IS_EDX_DOMAIN'] = True  # Is this an edX-owned domain? (used on instructor dashboard)
FEATURES['ENABLE_PAYMENT_FAKE'] = True


FEEDBACK_SUBMISSION_EMAIL = "dummy@example.com"

WIKI_ENABLED = True

DJFS = {
    'type': 'osfs',
    'directory_root': 'lms/static/djpyfs',
    'url_root': '/static/djpyfs'
}

# If there is a database called 'read_replica', you can use the use_read_replica_if_available
# function in util/query.py, which is useful for very large database reads
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ENV_ROOT / "db" / "edx.db",
        'ATOMIC_REQUESTS': True,
    }
}

CACHES = {
    # This is the cache used for most things.
    # In staging/prod envs, the sessions also live here.
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'edx_loc_mem_cache',
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
    },

    'mongo_metadata_inheritance': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/tmp/mongo_metadata_inheritance',
        'TIMEOUT': 300,
        'KEY_FUNCTION': 'util.memcache.safe_key',
    },
    'loc_cache': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'edx_location_mem_cache',
    },
    'course_structure_cache': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'edx_course_structure_mem_cache',
    },
    'lms.course_blocks': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'KEY_FUNCTION': 'util.memcache.safe_key',
        'LOCATION': 'lms_course_blocks_cache',
    },
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
    'berkeley': ['BerkeleyX/CS169/fa12',
                 'BerkeleyX/CS188/fa12'],
    'harvard': ['HarvardX/CS50x/2012H'],
    'mit': ['MITx/3.091/MIT_2012_Fall'],
    'sjsu': ['MITx/6.002x-EE98/2012_Fall_SJSU'],
}


SUBDOMAIN_BRANDING = {
    'sjsu': 'MITx',
    'mit': 'MITx',
    'berkeley': 'BerkeleyX',
    'harvard': 'HarvardX',
    'openedx': 'openedx',
    'edge': 'edge',
}

# List of `university` landing pages to display, even though they may not
# have an actual course with that org set
VIRTUAL_UNIVERSITIES = []

# Organization that contain other organizations
META_UNIVERSITIES = {'UTx': ['UTAustinX']}

COMMENTS_SERVICE_KEY = "PUT_YOUR_API_KEY_HERE"

############################## Course static files ##########################
if os.path.isdir(DATA_DIR):
    # Add the full course repo if there is no static directory
    STATICFILES_DIRS += [
        # TODO (cpennington): When courses are stored in a database, this
        # should no longer be added to STATICFILES
        (course_dir, DATA_DIR / course_dir)
        for course_dir in os.listdir(DATA_DIR)
        if (os.path.isdir(DATA_DIR / course_dir) and
            not os.path.isdir(DATA_DIR / course_dir / 'static'))
    ]
    # Otherwise, add only the static directory from the course dir
    STATICFILES_DIRS += [
        # TODO (cpennington): When courses are stored in a database, this
        # should no longer be added to STATICFILES
        (course_dir, DATA_DIR / course_dir / 'static')
        for course_dir in os.listdir(DATA_DIR)
        if (os.path.isdir(DATA_DIR / course_dir / 'static'))
    ]


################################# edx-platform revision string  #####################

EDX_PLATFORM_VERSION_STRING = os.popen('cd %s; git describe' % REPO_ROOT).read().strip()

############################ Open ended grading config  #####################

OPEN_ENDED_GRADING_INTERFACE = {
    'url': 'http://127.0.0.1:3033/',
    'username': 'lms',
    'password': 'abcd',
    'staff_grading': 'staff_grading',
    'peer_grading': 'peer_grading',
    'grading_controller': 'grading_controller'
}

############################## LMS Migration ##################################
FEATURES['ENABLE_LMS_MIGRATION'] = True
FEATURES['ACCESS_REQUIRE_STAFF_FOR_COURSE'] = False   # require that user be in the staff_* group to be able to enroll
FEATURES['XQA_SERVER'] = 'http://xqa:server@content-qa.edX.mit.edu/xqa'

INSTALLED_APPS += ('lms_migration',)

LMS_MIGRATION_ALLOWED_IPS = ['127.0.0.1']

################################ OpenID Auth #################################

FEATURES['AUTH_USE_OPENID'] = True
FEATURES['AUTH_USE_OPENID_PROVIDER'] = True
FEATURES['BYPASS_ACTIVATION_EMAIL_FOR_EXTAUTH'] = True

OPENID_CREATE_USERS = False
OPENID_UPDATE_DETAILS_FROM_SREG = True
OPENID_SSO_SERVER_URL = 'https://www.google.com/accounts/o8/id'  # TODO: accept more endpoints
OPENID_USE_AS_ADMIN_LOGIN = False

OPENID_PROVIDER_TRUSTED_ROOTS = ['*']

############################## OAUTH2 Provider ################################
FEATURES['ENABLE_OAUTH2_PROVIDER'] = True

######################## MIT Certificates SSL Auth ############################

FEATURES['AUTH_USE_CERTIFICATES'] = False

########################### External REST APIs #################################
FEATURES['ENABLE_MOBILE_REST_API'] = True
FEATURES['ENABLE_VIDEO_ABSTRACTION_LAYER_API'] = True

################################# CELERY ######################################

# By default don't use a worker, execute tasks as if they were local functions
CELERY_ALWAYS_EAGER = True

################################ DEBUG TOOLBAR ################################

INSTALLED_APPS += ('debug_toolbar', 'djpyfs',)
MIDDLEWARE_CLASSES += (
    'django_comment_client.utils.QueryCountDebugMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)
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

#################### FILE UPLOADS (for discussion forums) #####################

DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_ROOT = ENV_ROOT / "uploads"
MEDIA_URL = "/static/uploads/"
STATICFILES_DIRS.append(("uploads", MEDIA_ROOT))
FILE_UPLOAD_TEMP_DIR = ENV_ROOT / "uploads"
FILE_UPLOAD_HANDLERS = (
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
)

FEATURES['AUTH_USE_SHIB'] = True
FEATURES['RESTRICT_ENROLL_BY_REG_METHOD'] = True

########################### PIPELINE #################################

PIPELINE_SASS_ARGUMENTS = '--debug-info --require {proj_dir}/static/sass/bourbon/lib/bourbon.rb'.format(proj_dir=PROJECT_ROOT)

########################## ANALYTICS TESTING ########################

ANALYTICS_SERVER_URL = "http://127.0.0.1:9000/"
ANALYTICS_API_KEY = ""

##### Segment  ######

# If there's an environment variable set, grab it
LMS_SEGMENT_KEY = os.environ.get('SEGMENT_KEY')

###################### Payment ######################

CC_PROCESSOR['CyberSource']['SHARED_SECRET'] = os.environ.get('CYBERSOURCE_SHARED_SECRET', '')
CC_PROCESSOR['CyberSource']['MERCHANT_ID'] = os.environ.get('CYBERSOURCE_MERCHANT_ID', '')
CC_PROCESSOR['CyberSource']['SERIAL_NUMBER'] = os.environ.get('CYBERSOURCE_SERIAL_NUMBER', '')
CC_PROCESSOR['CyberSource']['PURCHASE_ENDPOINT'] = '/shoppingcart/payment_fake/'

CC_PROCESSOR['CyberSource2']['SECRET_KEY'] = os.environ.get('CYBERSOURCE_SECRET_KEY', '')
CC_PROCESSOR['CyberSource2']['ACCESS_KEY'] = os.environ.get('CYBERSOURCE_ACCESS_KEY', '')
CC_PROCESSOR['CyberSource2']['PROFILE_ID'] = os.environ.get('CYBERSOURCE_PROFILE_ID', '')
CC_PROCESSOR['CyberSource2']['PURCHASE_ENDPOINT'] = '/shoppingcart/payment_fake/'

########################## USER API ##########################
EDX_API_KEY = None

####################### Shoppingcart ###########################
FEATURES['ENABLE_SHOPPING_CART'] = True

### This enables the Metrics tab for the Instructor dashboard ###########
FEATURES['CLASS_DASHBOARD'] = True

### This settings is for the course registration code length ############
REGISTRATION_CODE_LENGTH = 8

#####################################################################
# Lastly, see if the developer has any local overrides.
try:
    from .private import *      # pylint: disable=import-error
except ImportError:
    pass
