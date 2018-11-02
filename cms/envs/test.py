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

from django.utils.translation import ugettext_lazy

from .common import *
import os
from path import Path as path
from uuid import uuid4
from util.db import NoOpMigrationModules
from openedx.core.lib.derived import derive_settings

# import settings from LMS for consistent behavior with CMS
# pylint: disable=unused-import
from lms.envs.test import (
    WIKI_ENABLED,
    PLATFORM_NAME,
    PLATFORM_DESCRIPTION,
    SITE_NAME,
    DEFAULT_FILE_STORAGE,
    MEDIA_ROOT,
    MEDIA_URL,
    COMPREHENSIVE_THEME_DIRS,
    JWT_AUTH,
    REGISTRATION_EXTRA_FIELDS,
    ECOMMERCE_API_URL,
    PROCTORING_BACKENDS,
)


# Include a non-ascii character in STUDIO_NAME and STUDIO_SHORT_NAME to uncover possible
# UnicodeEncodeErrors in tests. Also use lazy text to reveal possible json dumps errors
STUDIO_NAME = ugettext_lazy(u"Your Platform 𝓢𝓽𝓾𝓭𝓲𝓸")
STUDIO_SHORT_NAME = ugettext_lazy(u"𝓢𝓽𝓾𝓭𝓲𝓸")

# Allow all hosts during tests, we use a lot of different ones all over the codebase.
ALLOWED_HOSTS = [
    '*'
]

# mongo connection settings
MONGO_PORT_NUM = int(os.environ.get('EDXAPP_TEST_MONGO_PORT', '27017'))
MONGO_HOST = os.environ.get('EDXAPP_TEST_MONGO_HOST', 'localhost')

THIS_UUID = uuid4().hex[:5]

TEST_ROOT = path('test_root')

# Want static files in the same dir for running on jenkins.
STATIC_ROOT = TEST_ROOT / "staticfiles"
WEBPACK_LOADER['DEFAULT']['STATS_FILE'] = STATIC_ROOT / "webpack-stats.json"

GITHUB_REPO_ROOT = TEST_ROOT / "data"
DATA_DIR = TEST_ROOT / "data"
COMMON_TEST_DATA_ROOT = COMMON_ROOT / "test" / "data"

# For testing "push to lms"
FEATURES['ENABLE_EXPORT_GIT'] = True
GIT_REPO_EXPORT_DIR = TEST_ROOT / "export_course_repos"

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
        'db': 'test_xmodule_{}'.format(THIS_UUID),
        'host': MONGO_HOST,
        'port': MONGO_PORT_NUM,
        'collection': 'test_modulestore',
    },
)

CONTENTSTORE = {
    'ENGINE': 'xmodule.contentstore.mongo.MongoContentStore',
    'DOC_STORE_CONFIG': {
        'host': MONGO_HOST,
        'db': 'test_xcontent_{}'.format(THIS_UUID),
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

if os.environ.get('DISABLE_MIGRATIONS'):
    # Create tables directly from apps' models. This can be removed once we upgrade
    # to Django 1.9, which allows setting MIGRATION_MODULES to None in order to skip migrations.
    MIGRATION_MODULES = NoOpMigrationModules()

LMS_BASE = "localhost:8000"
LMS_ROOT_URL = "http://{}".format(LMS_BASE)
FEATURES['PREVIEW_LMS_BASE'] = "preview.localhost"


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

################################# CELERY ######################################

CELERY_ALWAYS_EAGER = True
CELERY_RESULT_BACKEND = 'djcelery.backends.cache:CacheBackend'

CLEAR_REQUEST_CACHE_ON_TASK_COMPLETION = False

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
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# No segment key
CMS_SEGMENT_KEY = None

FEATURES['DISABLE_SET_JWT_COOKIES_FOR_TESTS'] = True

FEATURES['ENABLE_SERVICE_STATUS'] = True

# Toggles embargo on for testing
FEATURES['EMBARGO'] = True

FEATURES['ENABLE_COMBINED_LOGIN_REGISTRATION'] = True

# set up some testing for microsites
FEATURES['USE_MICROSITES'] = True
MICROSITE_ROOT_DIR = COMMON_ROOT / 'test' / 'test_sites'
MICROSITE_CONFIGURATION = {
    "test_site": {
        "domain_prefix": "test-site",
        "university": "test_site",
        "platform_name": "Test Site",
        "logo_image_url": "test_site/images/header-logo.png",
        "email_from_address": "test_site@edx.org",
        "payment_support_email": "test_site@edx.org",
        "ENABLE_MKTG_SITE": False,
        "SITE_NAME": "test_site.localhost",
        "course_org_filter": "TestSiteX",
        "course_about_show_social_links": False,
        "css_overrides_file": "test_site/css/test_site.css",
        "show_partners": False,
        "show_homepage_promo_video": False,
        "course_index_overlay_text": "This is a Test Site Overlay Text.",
        "course_index_overlay_logo_file": "test_site/images/header-logo.png",
        "homepage_overlay_html": "<h1>This is a Test Site Overlay HTML</h1>",
        "ALWAYS_REDIRECT_HOMEPAGE_TO_DASHBOARD_FOR_AUTHENTICATED_USER": False,
        "COURSE_CATALOG_VISIBILITY_PERMISSION": "see_in_catalog",
        "COURSE_ABOUT_VISIBILITY_PERMISSION": "see_about_page",
        "ENABLE_SHOPPING_CART": True,
        "ENABLE_PAID_COURSE_REGISTRATION": True,
        "SESSION_COOKIE_DOMAIN": "test_site.localhost",
        "urls": {
            'ABOUT': 'test-site/about',
            'PRIVACY': 'test-site/privacy',
            'TOS_AND_HONOR': 'test-site/tos-and-honor',
        },
    },
    "site_with_logistration": {
        "domain_prefix": "logistration",
        "university": "logistration",
        "platform_name": "Test logistration",
        "logo_image_url": "test_site/images/header-logo.png",
        "email_from_address": "test_site@edx.org",
        "payment_support_email": "test_site@edx.org",
        "ENABLE_MKTG_SITE": False,
        "ENABLE_COMBINED_LOGIN_REGISTRATION": True,
        "SITE_NAME": "test_site.localhost",
        "course_org_filter": "LogistrationX",
        "course_about_show_social_links": False,
        "css_overrides_file": "test_site/css/test_site.css",
        "show_partners": False,
        "show_homepage_promo_video": False,
        "course_index_overlay_text": "Logistration.",
        "course_index_overlay_logo_file": "test_site/images/header-logo.png",
        "homepage_overlay_html": "<h1>This is a Logistration HTML</h1>",
        "ALWAYS_REDIRECT_HOMEPAGE_TO_DASHBOARD_FOR_AUTHENTICATED_USER": False,
        "COURSE_CATALOG_VISIBILITY_PERMISSION": "see_in_catalog",
        "COURSE_ABOUT_VISIBILITY_PERMISSION": "see_about_page",
        "ENABLE_SHOPPING_CART": True,
        "ENABLE_PAID_COURSE_REGISTRATION": True,
        "SESSION_COOKIE_DOMAIN": "test_logistration.localhost",
    },
    "default": {
        "university": "default_university",
        "domain_prefix": "www",
    }
}
MICROSITE_TEST_HOSTNAME = 'test-site.testserver'
MICROSITE_LOGISTRATION_HOSTNAME = 'logistration.testserver'

TEST_THEME = COMMON_ROOT / "test" / "test-theme"

# For consistency in user-experience, keep the value of this setting in sync with
# the one in lms/envs/test.py
FEATURES['ENABLE_DISCUSSION_SERVICE'] = False

# Enable a parental consent age limit for testing
PARENTAL_CONSENT_AGE_LIMIT = 13

# Enable certificates for the tests
FEATURES['CERTIFICATES_HTML_VIEW'] = True

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

FEATURES['ENABLE_ENROLLMENT_TRACK_USER_PARTITION'] = True

########################## AUTHOR PERMISSION #######################
FEATURES['ENABLE_CREATOR_GROUP'] = False

# teams feature
FEATURES['ENABLE_TEAMS'] = True

# Dummy secret key for dev/test
SECRET_KEY = '85920908f28904ed733fe576320db18cabd7b6cd'

######### custom courses #########
INSTALLED_APPS.append('openedx.core.djangoapps.ccxcon.apps.CCXConnectorConfig')
FEATURES['CUSTOM_COURSES_EDX'] = True

########################## VIDEO IMAGE STORAGE ############################
VIDEO_IMAGE_SETTINGS = dict(
    VIDEO_IMAGE_MAX_BYTES=2 * 1024 * 1024,    # 2 MB
    VIDEO_IMAGE_MIN_BYTES=2 * 1024,       # 2 KB
    STORAGE_KWARGS=dict(
        location=MEDIA_ROOT,
        base_url=MEDIA_URL,
    ),
    DIRECTORY_PREFIX='video-images/',
)
VIDEO_IMAGE_DEFAULT_FILENAME = 'default_video_image.png'

########################## VIDEO TRANSCRIPTS STORAGE ############################
VIDEO_TRANSCRIPTS_SETTINGS = dict(
    VIDEO_TRANSCRIPTS_MAX_BYTES=3 * 1024 * 1024,    # 3 MB
    STORAGE_KWARGS=dict(
        location=MEDIA_ROOT,
        base_url=MEDIA_URL,
    ),
    DIRECTORY_PREFIX='video-transcripts/',
)

####################### Plugin Settings ##########################

from openedx.core.djangoapps.plugins import plugin_settings, constants as plugin_constants
plugin_settings.add_plugins(__name__, plugin_constants.ProjectType.CMS, plugin_constants.SettingsType.TEST)

########################## Derive Any Derived Settings  #######################

derive_settings(__name__)
