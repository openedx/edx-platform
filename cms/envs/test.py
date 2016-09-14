# -*- coding: utf-8 -*-
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

# Pylint gets confused by path.py instances, which report themselves as class
# objects. As a result, pylint applies the wrong regex in validating names,
# and throws spurious errors. Therefore, we disable invalid-name checking.
# pylint: disable=invalid-name

from .common import *
import os
from path import Path as path
from warnings import filterwarnings, simplefilter
from uuid import uuid4

# import settings from LMS for consistent behavior with CMS
# pylint: disable=unused-import
from lms.envs.test import (
    WIKI_ENABLED,
    PLATFORM_NAME,
    SITE_NAME,
    DEFAULT_FILE_STORAGE,
    MEDIA_ROOT,
    MEDIA_URL,
    # This is practically unused but needed by the oauth2_provider package, which
    # some tests in common/ rely on.
    OAUTH_OIDC_ISSUER,
)

# mongo connection settings
MONGO_PORT_NUM = int(os.environ.get('EDXAPP_TEST_MONGO_PORT', '27017'))
MONGO_HOST = os.environ.get('EDXAPP_TEST_MONGO_HOST', 'localhost')

# Remove sneakpeek during tests to prevent unwanted redirect
MIDDLEWARE_CLASSES = tuple([
    mwc for mwc in MIDDLEWARE_CLASSES
    if mwc != 'sneakpeek.middleware.SneakPeekLogoutMiddleware'
])

THIS_UUID = uuid4().hex[:5]

# Nose Test Runner
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

_SYSTEM = 'cms'

_REPORT_DIR = REPO_ROOT / 'reports' / _SYSTEM
_REPORT_DIR.makedirs_p()
_NOSEID_DIR = REPO_ROOT / '.testids' / _SYSTEM
_NOSEID_DIR.makedirs_p()

NOSE_ARGS = [
    '--id-file', _NOSEID_DIR / 'noseids',
    '--xunit-file', _REPORT_DIR / 'nosetests.xml',
]

TEST_ROOT = path('test_root')

# Want static files in the same dir for running on jenkins.
STATIC_ROOT = TEST_ROOT / "staticfiles"

GITHUB_REPO_ROOT = TEST_ROOT / "data"
DATA_DIR = TEST_ROOT / "data"
COMMON_TEST_DATA_ROOT = COMMON_ROOT / "test" / "data"

# For testing "push to lms"
FEATURES['ENABLE_EXPORT_GIT'] = True
GIT_REPO_EXPORT_DIR = TEST_ROOT / "export_course_repos"

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

# Avoid having to run collectstatic before the unit test suite
# If we don't add these settings, then Django templates that can't
# find pipelined assets will raise a ValueError.
# http://stackoverflow.com/questions/12816941/unit-testing-with-django-pipeline
STATICFILES_STORAGE = 'pipeline.storage.NonPackagingPipelineStorage'
STATIC_URL = "/static/"

# Update module store settings per defaults for tests
update_module_store_settings(
    MODULESTORE,
    module_store_options={
        'default_class': 'xmodule.raw_module.RawDescriptor',
        'fs_root': TEST_ROOT / "data",
    },
    doc_store_settings={
        'db': 'test_xmodule',
        'host': MONGO_HOST,
        'port': MONGO_PORT_NUM,
        'collection': 'test_modulestore{0}'.format(THIS_UUID),
    },
)

CONTENTSTORE = {
    'ENGINE': 'xmodule.contentstore.mongo.MongoContentStore',
    'DOC_STORE_CONFIG': {
        'host': MONGO_HOST,
        'db': 'test_xcontent',
        'port': MONGO_PORT_NUM,
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
        'ATOMIC_REQUESTS': True,
    },
}

# This hack disables migrations during tests. We want to create tables directly from the models for speed.
# See https://groups.google.com/d/msg/django-developers/PWPj3etj3-U/kCl6pMsQYYoJ.
MIGRATION_MODULES = {app: "app.migrations_not_used_in_tests" for app in INSTALLED_APPS}

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
        'LOCATION': os.path.join(tempfile.gettempdir(), 'mongo_metadata_inheritance'),
        'TIMEOUT': 300,
        'KEY_FUNCTION': 'util.memcache.safe_key',
    },
    'loc_cache': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'edx_location_mem_cache',
    },
    'course_structure_cache': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
}

# Add apps to Installed apps for testing
INSTALLED_APPS += ('openedx.core.djangoapps.call_stack_manager',)

# hide ratelimit warnings while running tests
filterwarnings('ignore', message='No request passed to the backend, unable to rate-limit')

# Ignore deprecation warnings (so we don't clutter Jenkins builds/production)
# https://docs.python.org/2/library/warnings.html#the-warnings-filter
# Change to "default" to see the first instance of each hit
# or "error" to convert all into errors
simplefilter('ignore')

################################# CELERY ######################################

CELERY_ALWAYS_EAGER = True
CELERY_RESULT_BACKEND = 'djcelery.backends.cache:CacheBackend'

########################### Server Ports ###################################

# These ports are carefully chosen so that if the browser needs to
# access them, they will be available through the SauceLabs SSH tunnel
LETTUCE_SERVER_PORT = 8003
XQUEUE_PORT = 8040
YOUTUBE_PORT = 8031
LTI_PORT = 8765
VIDEO_SOURCE_PORT = 8777


################### Make tests faster
# http://slacy.com/blog/2012/04/make-your-tests-faster-in-django-1-4/
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

# No segment key
CMS_SEGMENT_KEY = None

FEATURES['ENABLE_SERVICE_STATUS'] = True

# Toggles embargo on for testing
FEATURES['EMBARGO'] = True

# set up some testing for microsites
MICROSITE_CONFIGURATION = {
    "test_microsite": {
        "domain_prefix": "testmicrosite",
        "university": "test_microsite",
        "platform_name": "Test Microsite",
        "logo_image_url": "test_microsite/images/header-logo.png",
        "email_from_address": "test_microsite@edx.org",
        "payment_support_email": "test_microsite@edx.org",
        "ENABLE_MKTG_SITE": False,
        "SITE_NAME": "test_microsite.localhost",
        "course_org_filter": "TestMicrositeX",
        "course_about_show_social_links": False,
        "css_overrides_file": "test_microsite/css/test_microsite.css",
        "show_partners": False,
        "show_homepage_promo_video": False,
        "course_index_overlay_text": "This is a Test Microsite Overlay Text.",
        "course_index_overlay_logo_file": "test_microsite/images/header-logo.png",
        "homepage_overlay_html": "<h1>This is a Test Microsite Overlay HTML</h1>"
    },
    "default": {
        "university": "default_university",
        "domain_prefix": "www",
    }
}
MICROSITE_ROOT_DIR = COMMON_ROOT / 'test' / 'test_microsites'
FEATURES['USE_MICROSITES'] = True

# For consistency in user-experience, keep the value of this setting in sync with
# the one in lms/envs/test.py
FEATURES['ENABLE_DISCUSSION_SERVICE'] = False

# Enable a parental consent age limit for testing
PARENTAL_CONSENT_AGE_LIMIT = 13

# Enable content libraries code for the tests
FEATURES['ENABLE_CONTENT_LIBRARIES'] = True

FEATURES['ENABLE_EDXNOTES'] = True

# MILESTONES
FEATURES['MILESTONES_APP'] = True

# ENTRANCE EXAMS
FEATURES['ENTRANCE_EXAMS'] = True
ENTRANCE_EXAM_MIN_SCORE_PCT = 50

VIDEO_CDN_URL = {
    'CN': 'http://api.xuetangx.com/edx/video?s3_url='
}

# Courseware Search Index
FEATURES['ENABLE_COURSEWARE_INDEX'] = True
FEATURES['ENABLE_LIBRARY_INDEX'] = True
SEARCH_ENGINE = "search.tests.mock_search_engine.MockSearchEngine"


# teams feature
FEATURES['ENABLE_TEAMS'] = True

# Dummy secret key for dev/test
SECRET_KEY = '85920908f28904ed733fe576320db18cabd7b6cd'
