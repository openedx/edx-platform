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
# pylint: disable=W0401, W0614

from .common import *
import os
from path import path
from warnings import filterwarnings

# Nose Test Runner
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

_system = 'cms'
_report_dir = REPO_ROOT / 'reports' / _system
_report_dir.makedirs_p()

NOSE_ARGS = [
    '--id-file', REPO_ROOT / '.testids' / _system / 'noseids',
    '--xunit-file', _report_dir / 'nosetests.xml',
]

TEST_ROOT = path('test_root')

# Want static files in the same dir for running on jenkins.
STATIC_ROOT = TEST_ROOT / "staticfiles"

GITHUB_REPO_ROOT = TEST_ROOT / "data"
COMMON_TEST_DATA_ROOT = COMMON_ROOT / "test" / "data"

# Makes the tests run much faster...
SOUTH_TESTS_MIGRATE = False  # To disable migrations and use syncdb instead

# TODO (cpennington): We need to figure out how envs/test.py can inject things into common.py so that we don't have to repeat this sort of thing
STATICFILES_DIRS = [
    COMMON_ROOT / "static",
    PROJECT_ROOT / "static",
]
STATICFILES_DIRS += [
    (course_dir, COMMON_TEST_DATA_ROOT / course_dir)
    for course_dir in os.listdir(COMMON_TEST_DATA_ROOT)
    if os.path.isdir(COMMON_TEST_DATA_ROOT / course_dir)
]

DOC_STORE_CONFIG = {
    'host': 'localhost',
    'db': 'test_xmodule',
    'collection': 'test_modulestore',
}

MODULESTORE_OPTIONS = {
    'default_class': 'xmodule.raw_module.RawDescriptor',
    'fs_root': TEST_ROOT / "data",
    'render_template': 'edxmako.shortcuts.render_to_string',
}

MODULESTORE = {
    'default': {
        'ENGINE': 'xmodule.modulestore.draft.DraftModuleStore',
        'DOC_STORE_CONFIG': DOC_STORE_CONFIG,
        'OPTIONS': MODULESTORE_OPTIONS
    },
    'direct': {
        'ENGINE': 'xmodule.modulestore.mongo.MongoModuleStore',
        'DOC_STORE_CONFIG': DOC_STORE_CONFIG,
        'OPTIONS': MODULESTORE_OPTIONS
    },
    'draft': {
        'ENGINE': 'xmodule.modulestore.draft.DraftModuleStore',
        'DOC_STORE_CONFIG': DOC_STORE_CONFIG,
        'OPTIONS': MODULESTORE_OPTIONS
    },
    'split': {
        'ENGINE': 'xmodule.modulestore.split_mongo.SplitMongoModuleStore',
        'DOC_STORE_CONFIG': DOC_STORE_CONFIG,
        'OPTIONS': MODULESTORE_OPTIONS
    }
}

CONTENTSTORE = {
    'ENGINE': 'xmodule.contentstore.mongo.MongoContentStore',
    'DOC_STORE_CONFIG': {
        'host': 'localhost',
        'db': 'test_xcontent',
        'collection': 'dont_trip',
    },
    # allow for additional options that can be keyed on a name, e.g. 'trashcan'
    'ADDITIONAL_OPTIONS': {
        'trashcan': {
            'bucket': 'trash_fs'
        }
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': TEST_ROOT / "db" / "cms.db",
    },
}

LMS_BASE = "localhost:8000"
FEATURES['PREVIEW_LMS_BASE'] = "preview"

CACHES = {
    # This is the cache used for most things. Askbot will not work without a
    # functioning cache -- it relies on caching to load its settings in places.
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
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': '/var/tmp/mongo_metadata_inheritance',
        'TIMEOUT': 300,
        'KEY_FUNCTION': 'util.memcache.safe_key',
    },
    'loc_cache': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'edx_location_mem_cache',
    },

}

# Add external_auth to Installed apps for testing
INSTALLED_APPS += ('external_auth', )

# hide ratelimit warnings while running tests
filterwarnings('ignore', message='No request passed to the backend, unable to rate-limit')

################################# CELERY ######################################

CELERY_ALWAYS_EAGER = True
CELERY_RESULT_BACKEND = 'cache'
BROKER_TRANSPORT = 'memory'


########################### Server Ports ###################################

# These ports are carefully chosen so that if the browser needs to
# access them, they will be available through the SauceLabs SSH tunnel
LETTUCE_SERVER_PORT = 8003
XQUEUE_PORT = 8040
YOUTUBE_PORT = 8031
LTI_PORT = 8765


################### Make tests faster
# http://slacy.com/blog/2012/04/make-your-tests-faster-in-django-1-4/
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

# dummy segment-io key
SEGMENT_IO_KEY = '***REMOVED***'

# disable NPS survey in test mode
FEATURES['STUDIO_NPS_SURVEY'] = False

FEATURES['ENABLE_SERVICE_STATUS'] = True

# This is to disable a test under the common directory that will not pass when run under CMS
FEATURES['DISABLE_RESET_EMAIL_TEST'] = True
