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


import os
from uuid import uuid4

from django.utils.translation import gettext_lazy
from path import Path as path

from openedx.core.lib.derived import derive_settings

from xmodule.modulestore.modulestore_settings import update_module_store_settings  # pylint: disable=wrong-import-order

from .common import *

# import settings from LMS for consistent behavior with CMS
from lms.envs.test import (  # pylint: disable=wrong-import-order
    BLOCKSTORE_USE_BLOCKSTORE_APP_API,
    BLOCKSTORE_API_URL,
    COMPREHENSIVE_THEME_DIRS,  # unimport:skip
    DEFAULT_FILE_STORAGE,
    ECOMMERCE_API_URL,
    ENABLE_COMPREHENSIVE_THEMING,
    JWT_AUTH,
    LOGIN_ISSUE_SUPPORT_LINK,
    MEDIA_ROOT,
    MEDIA_URL,
    PLATFORM_DESCRIPTION,
    PLATFORM_NAME,
    REGISTRATION_EXTRA_FIELDS,
    GRADES_DOWNLOAD,
    SITE_NAME,
    WIKI_ENABLED,
    XBLOCK_RUNTIME_V2_EPHEMERAL_DATA_CACHE,
)


# Include a non-ascii character in STUDIO_NAME and STUDIO_SHORT_NAME to uncover possible
# UnicodeEncodeErrors in tests. Also use lazy text to reveal possible json dumps errors
STUDIO_NAME = gettext_lazy("Your Platform 𝓢𝓽𝓾𝓭𝓲𝓸")
STUDIO_SHORT_NAME = gettext_lazy("𝓢𝓽𝓾𝓭𝓲𝓸")

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

# TODO (cpennington): We need to figure out how envs/test.py can inject things into common.py so that we don't have to repeat this sort of thing  # lint-amnesty, pylint: disable=line-too-long
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

BLOCK_STRUCTURES_SETTINGS['PRUNING_ACTIVE'] = True

# Update module store settings per defaults for tests
update_module_store_settings(
    MODULESTORE,
    module_store_options={
        'default_class': 'xmodule.hidden_block.HiddenBlock',
        'fs_root': TEST_ROOT / "data",
    },
    doc_store_settings={
        'db': f'test_xmodule_{THIS_UUID}',
        'host': MONGO_HOST,
        'port': MONGO_PORT_NUM,
        'collection': 'test_modulestore',
    },
)

CONTENTSTORE = {
    'ENGINE': 'xmodule.contentstore.mongo.MongoContentStore',
    'DOC_STORE_CONFIG': {
        'host': MONGO_HOST,
        'db': f'test_xcontent_{THIS_UUID}',
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

LMS_BASE = "localhost:8000"
LMS_ROOT_URL = f"http://{LMS_BASE}"
FEATURES['PREVIEW_LMS_BASE'] = "preview.localhost"

COURSE_AUTHORING_MICROFRONTEND_URL = "http://course-authoring-mfe"
DISCUSSIONS_MICROFRONTEND_URL = "http://discussions-mfe"

CACHES = {
    # This is the cache used for most things. Askbot will not work without a
    # functioning cache -- it relies on caching to load its settings in places.
    # In staging/prod envs, the sessions also live here.
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'edx_loc_mem_cache',
        'KEY_FUNCTION': 'common.djangoapps.util.memcache.safe_key',
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
        'KEY_FUNCTION': 'common.djangoapps.util.memcache.safe_key',
    },

    'mongo_metadata_inheritance': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': os.path.join(tempfile.gettempdir(), 'mongo_metadata_inheritance'),
        'TIMEOUT': 300,
        'KEY_FUNCTION': 'common.djangoapps.util.memcache.safe_key',
    },
    'loc_cache': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'edx_location_mem_cache',
    },
    'course_structure_cache': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    'blockstore': {
        'KEY_PREFIX': 'blockstore',
        'KEY_FUNCTION': 'common.djangoapps.util.memcache.safe_key',
        'LOCATION': 'edx_loc_mem_cache',
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
}

############################### BLOCKSTORE #####################################
# Blockstore tests
RUN_BLOCKSTORE_TESTS = os.environ.get('EDXAPP_RUN_BLOCKSTORE_TESTS', 'no').lower() in ('true', 'yes', '1')
BLOCKSTORE_API_URL = os.environ.get('EDXAPP_BLOCKSTORE_API_URL', "http://edx.devstack.blockstore-test:18251/api/v1/")
BLOCKSTORE_API_AUTH_TOKEN = os.environ.get('EDXAPP_BLOCKSTORE_API_AUTH_TOKEN', 'edxapp-test-key')
BUNDLE_ASSET_STORAGE_SETTINGS = dict(
    STORAGE_CLASS='django.core.files.storage.FileSystemStorage',
    STORAGE_KWARGS=dict(
        location=MEDIA_ROOT,
        base_url=MEDIA_URL,
    ),
)

################################# CELERY ######################################

CELERY_ALWAYS_EAGER = True
CELERY_RESULT_BACKEND = 'django-cache'

CLEAR_REQUEST_CACHE_ON_TASK_COMPLETION = False

# test_status_cancel in cms/cms_user_tasks/test.py is failing without this
# @override_setting for BROKER_URL is not working in testcase, so updating here
BROKER_URL = 'memory://localhost/'

########################### Server Ports ###################################

# These ports are carefully chosen so that if the browser needs to
# access them, they will be available through the SauceLabs SSH tunnel
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
FEATURES['ENABLE_CONTENT_LIBRARY_INDEX'] = False
SEARCH_ENGINE = "search.tests.mock_search_engine.MockSearchEngine"

FEATURES['ENABLE_ENROLLMENT_TRACK_USER_PARTITION'] = True

####################### ELASTICSEARCH TESTS #######################
# Enable this when testing elasticsearch-based code which couldn't be tested using the mock engine
ENABLE_ELASTICSEARCH_FOR_TESTS = os.environ.get(
    'EDXAPP_ENABLE_ELASTICSEARCH_FOR_TESTS', 'no').lower() in ('true', 'yes', '1')

TEST_ELASTICSEARCH_USE_SSL = os.environ.get(
    'EDXAPP_TEST_ELASTICSEARCH_USE_SSL', 'no').lower() in ('true', 'yes', '1')
TEST_ELASTICSEARCH_HOST = os.environ.get('EDXAPP_TEST_ELASTICSEARCH_HOST', 'edx.devstack.elasticsearch710')
TEST_ELASTICSEARCH_PORT = int(os.environ.get('EDXAPP_TEST_ELASTICSEARCH_PORT', '9200'))

########################## AUTHOR PERMISSION #######################
FEATURES['ENABLE_CREATOR_GROUP'] = False

# teams feature
FEATURES['ENABLE_TEAMS'] = True

# Dummy secret key for dev/test
SECRET_KEY = '85920908f28904ed733fe576320db18cabd7b6cd'

######### custom courses #########
INSTALLED_APPS += [
    'openedx.core.djangoapps.ccxcon.apps.CCXConnectorConfig',
    'common.djangoapps.third_party_auth.apps.ThirdPartyAuthConfig',
]
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

# pylint: disable=wrong-import-position, wrong-import-order
from edx_django_utils.plugins import add_plugins
# pylint: disable=wrong-import-position, wrong-import-order
from openedx.core.djangoapps.plugins.constants import ProjectType, SettingsType
add_plugins(__name__, ProjectType.CMS, SettingsType.TEST)

########################## Derive Any Derived Settings  #######################

derive_settings(__name__)

############### Settings for edx-rbac  ###############
SYSTEM_WIDE_ROLE_CLASSES = os.environ.get("SYSTEM_WIDE_ROLE_CLASSES", [])

DEFAULT_MOBILE_AVAILABLE = True

PROCTORING_SETTINGS = {}

# Used in edx-proctoring for ID generation in lieu of SECRET_KEY - dummy value
# (ref MST-637)
PROCTORING_USER_OBFUSCATION_KEY = '85920908f28904ed733fe576320db18cabd7b6cd'

##### LOGISTRATION RATE LIMIT SETTINGS #####
LOGISTRATION_RATELIMIT_RATE = '5/5m'
LOGISTRATION_PER_EMAIL_RATELIMIT_RATE = '6/5m'
LOGISTRATION_API_RATELIMIT = '5/m'

REGISTRATION_VALIDATION_RATELIMIT = '5/minute'
REGISTRATION_RATELIMIT = '5/minute'
OPTIONAL_FIELD_API_RATELIMIT = '5/m'

RESET_PASSWORD_TOKEN_VALIDATE_API_RATELIMIT = '2/m'
RESET_PASSWORD_API_RATELIMIT = '2/m'

############### Settings for proctoring  ###############
PROCTORING_USER_OBFUSCATION_KEY = 'test_key'

#################### Network configuration ####################
# Tests are not behind any proxies
CLOSEST_CLIENT_IP_FROM_HEADERS = []

COURSE_LIVE_GLOBAL_CREDENTIALS["BIG_BLUE_BUTTON"] = {
    "KEY": "***",
    "SECRET": "***",
    "URL": "***",
}
