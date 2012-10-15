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
import os
from path import path

# can't test start dates with this True, but on the other hand,
# can test everything else :)
MITX_FEATURES['DISABLE_START_DATES'] = True

# Until we have discussion actually working in test mode, just turn it off
MITX_FEATURES['ENABLE_DISCUSSION_SERVICE'] = False

# Need wiki for courseware views to work. TODO (vshnayder): shouldn't need it.
WIKI_ENABLED = True

# Makes the tests run much faster...
SOUTH_TESTS_MIGRATE = False # To disable migrations and use syncdb instead

# Nose Test Runner
INSTALLED_APPS += ('django_nose',)
NOSE_ARGS = ['--cover-erase', '--with-xunit', '--with-xcoverage', '--cover-html',
             # '-v', '--pdb',     # When really stuck, uncomment to start debugger on error
             '--cover-inclusive', '--cover-html-dir',
             os.environ.get('NOSE_COVER_HTML_DIR', 'cover_html')]
for app in os.listdir(PROJECT_ROOT / 'djangoapps'):
    NOSE_ARGS += ['--cover-package', app]
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

# Local Directories
TEST_ROOT = path("test_root")
# Want static files in the same dir for running on jenkins.
STATIC_ROOT = TEST_ROOT / "staticfiles"

STATUS_MESSAGE_PATH = TEST_ROOT / "status_message.json"

COURSES_ROOT = TEST_ROOT / "data"
DATA_DIR = COURSES_ROOT

LOGGING = get_logger_config(TEST_ROOT / "log",
                            logging_env="dev",
                            tracking_filename="tracking.log",
                            dev_env=True,
                            debug=True)

COMMON_TEST_DATA_ROOT = COMMON_ROOT / "test" / "data"
# Where the content data is checked out.  This may not exist on jenkins.
GITHUB_REPO_ROOT = ENV_ROOT / "data"


XQUEUE_INTERFACE = {
    "url": "http://sandbox-xqueue.edx.org",
    "django_auth": {
        "username": "lms",
        "password": "***REMOVED***"
    },
    "basic_auth": ('anant', 'agarwal'),
}
XQUEUE_WAITTIME_BETWEEN_REQUESTS = 5 # seconds

# TODO (cpennington): We need to figure out how envs/test.py can inject things
# into common.py so that we don't have to repeat this sort of thing
STATICFILES_DIRS = [
    COMMON_ROOT / "static",
    PROJECT_ROOT / "static",
    ASKBOT_ROOT / "askbot" / "skins",
]
STATICFILES_DIRS += [
    (course_dir, COMMON_TEST_DATA_ROOT / course_dir)
    for course_dir in os.listdir(COMMON_TEST_DATA_ROOT)
    if os.path.isdir(COMMON_TEST_DATA_ROOT / course_dir)
]

# point tests at the test courses by default

MODULESTORE = {
    'default': {
        'ENGINE': 'xmodule.modulestore.xml.XMLModuleStore',
        'OPTIONS': {
            'data_dir': COMMON_TEST_DATA_ROOT,
            'default_class': 'xmodule.hidden_module.HiddenDescriptor',
        }
    }
}


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': PROJECT_ROOT / "db" / "mitx.db",
    },

    # The following are for testing purposes...
    'edX/toy/2012_Fall': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ENV_ROOT / "db" / "course1.db",
    },

    'edx/full/6.002_Spring_2012': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ENV_ROOT / "db" / "course2.db",
    },

    'edX/toy/TT_2012_Fall': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ENV_ROOT / "db" / "course3.db",
    },

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

# Dummy secret key for dev
SECRET_KEY = '85920908f28904ed733fe576320db18cabd7b6cd'

################################## OPENID ######################################
MITX_FEATURES['AUTH_USE_OPENID'] = True
MITX_FEATURES['AUTH_USE_OPENID_PROVIDER'] = True
OPENID_PROVIDER_TRUSTED_ROOTS = ['*']

############################ FILE UPLOADS (ASKBOT) #############################
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_ROOT = TEST_ROOT / "uploads"
MEDIA_URL = "/static/uploads/"
STATICFILES_DIRS.append(("uploads", MEDIA_ROOT))

new_staticfiles_dirs = []
# Strip out any static files that aren't in the repository root
# so that the tests can run with only the mitx directory checked out
for static_dir in STATICFILES_DIRS:
    # Handle both tuples and non-tuple directory definitions
    try:
        _, data_dir = static_dir
    except ValueError:
        data_dir = static_dir

    if data_dir.startswith(REPO_ROOT):
        new_staticfiles_dirs.append(static_dir)
STATICFILES_DIRS = new_staticfiles_dirs

FILE_UPLOAD_TEMP_DIR = PROJECT_ROOT / "uploads"
FILE_UPLOAD_HANDLERS = (
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
)

################### Make tests faster

#http://slacy.com/blog/2012/04/make-your-tests-faster-in-django-1-4/
PASSWORD_HASHERS = (
    # 'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    # 'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    # 'django.contrib.auth.hashers.BCryptPasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
    # 'django.contrib.auth.hashers.CryptPasswordHasher',
)
