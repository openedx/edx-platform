"""
Settings for Bok Choy tests that are used when running LMS.

Bok Choy uses two different settings files:
1. test_static_optimized is used when invoking collectstatic
2. bok_choy is used when running the tests

Note: it isn't possible to have a single settings file, because Django doesn't
support both generating static assets to a directory and also serving static
from the same directory.
"""


# Silence noisy logs
import logging
import os
from tempfile import mkdtemp

from django.utils.translation import gettext_lazy
from path import Path as path

from openedx.core.release import RELEASE_LINE
from xmodule.modulestore.modulestore_settings import update_module_store_settings  # lint-amnesty, pylint: disable=wrong-import-order

CONFIG_ROOT = path(__file__).abspath().dirname()
TEST_ROOT = CONFIG_ROOT.dirname().dirname() / "test_root"

########################## Prod-like settings ###################################
# These should be as close as possible to the settings we use in production.
# As in prod, we read in environment and auth variables from JSON files.
# Unlike in prod, we use the JSON files stored in this repo.
# This is a convenience for ensuring (a) that we can consistently find the files
# and (b) that the files are the same in Jenkins as in local dev.
os.environ['SERVICE_VARIANT'] = 'bok_choy_docker' if 'BOK_CHOY_HOSTNAME' in os.environ else 'bok_choy'
os.environ['LMS_CFG'] = str.format("{config_root}/{service_variant}.yml",
                                   config_root=CONFIG_ROOT, service_variant=os.environ['SERVICE_VARIANT'])
os.environ['REVISION_CFG'] = f"{CONFIG_ROOT}/revisions.yml"

from .production import *  # pylint: disable=wildcard-import, unused-wildcard-import, wrong-import-position


######################### Testing overrides ####################################

# Redirect to the test_root folder within the repo
GITHUB_REPO_ROOT = (TEST_ROOT / "data").abspath()
LOG_DIR = (TEST_ROOT / "log").abspath()

# Configure modulestore to use the test folder within the repo
update_module_store_settings(
    MODULESTORE,
    module_store_options={
        'fs_root': (TEST_ROOT / "data").abspath(),
    },
    xml_store_options={
        'data_dir': (TEST_ROOT / "data").abspath(),
    },
    default_store=os.environ.get('DEFAULT_STORE', 'draft'),
)

PLATFORM_NAME = gettext_lazy("édX")
PLATFORM_DESCRIPTION = gettext_lazy("Open édX Platform")

############################ STATIC FILES #############################

# Serve static files at /static directly from the staticfiles directory under test root
# Note: optimized files for testing are generated with settings from test_static_optimized
STATIC_URL = "/static/"
STATICFILES_FINDERS = ['django.contrib.staticfiles.finders.FileSystemFinder']
STATICFILES_DIRS = [
    (TEST_ROOT / "staticfiles" / "lms").abspath(),
]

DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_ROOT = TEST_ROOT / "uploads"

# Webpack loader must use webpack output setting
WEBPACK_LOADER['DEFAULT']['STATS_FILE'] = TEST_ROOT / "staticfiles" / "lms" / "webpack-stats.json"

# Don't use compression during tests
PIPELINE['JS_COMPRESSOR'] = None

###################### Grades ######################
GRADES_DOWNLOAD = {
    'STORAGE_TYPE': 'localfs',
    'BUCKET': 'edx-grades',
    'ROOT_PATH': os.path.join(mkdtemp(), 'edx-s3', 'grades'),
}


LOG_OVERRIDES = [
    ('track.middleware', logging.CRITICAL),
    ('common.djangoapps.edxmako.shortcuts', logging.ERROR),
    ('edx.discussion', logging.CRITICAL),
]
for log_name, log_level in LOG_OVERRIDES:
    logging.getLogger(log_name).setLevel(log_level)


YOUTUBE_HOSTNAME = os.environ.get('BOK_CHOY_HOSTNAME', '127.0.0.1')
# Point the URL used to test YouTube availability to our stub YouTube server
YOUTUBE_PORT = 9080
YOUTUBE['TEST_TIMEOUT'] = 5000
YOUTUBE['API'] = f"http://{YOUTUBE_HOSTNAME}:{YOUTUBE_PORT}/get_youtube_api/"
YOUTUBE['METADATA_URL'] = f"http://{YOUTUBE_HOSTNAME}:{YOUTUBE_PORT}/test_youtube/"
YOUTUBE['TEXT_API']['url'] = f"{YOUTUBE_HOSTNAME}:{YOUTUBE_PORT}/test_transcripts_youtube/"

############################# SECURITY SETTINGS ################################
# Default to advanced security in common.py, so tests can reset here to use
# a simpler security model

# Path at which to store the mock index
MOCK_SEARCH_BACKING_FILE = (
    TEST_ROOT / "index_file.dat"
).abspath()

# Verify student settings
VERIFY_STUDENT["SOFTWARE_SECURE"] = {
    "API_ACCESS_KEY": "BBBBBBBBBBBBBBBBBBBB",
    "API_SECRET_KEY": "CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
}

# Set dummy values for profile image settings.
PROFILE_IMAGE_BACKEND = {
    'class': 'openedx.core.storage.OverwriteStorage',
    'options': {
        'location': os.path.join(MEDIA_ROOT, 'profile-images/'),
        'base_url': os.path.join(MEDIA_URL, 'profile-images/'),
    },
}

LMS_ROOT_URL = "http://localhost:{}".format(os.environ.get('BOK_CHOY_LMS_PORT', 8003))
CMS_BASE = "localhost:{}".format(os.environ.get('BOK_CHOY_CMS_PORT', 8031))
LOGIN_REDIRECT_WHITELIST = [CMS_BASE]

INSTALLED_APPS.append('openedx.testing.coverage_context_listener')

if RELEASE_LINE == "master":
    # On master, acceptance tests use edX books, not the default Open edX books.
    HELP_TOKENS_BOOKS = {
        'learner': 'https://edx.readthedocs.io/projects/edx-guide-for-students',
        'course_author': 'https://edx.readthedocs.io/projects/edx-partner-course-staff',
    }


#####################################################################
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

from uuid import uuid4
# mongo connection settings
MONGO_PORT_NUM = int(os.environ.get('EDXAPP_TEST_MONGO_PORT', '27017'))
MONGO_HOST = os.environ.get('EDXAPP_TEST_MONGO_HOST', 'localhost')

THIS_UUID = uuid4().hex[:5]

# Update module store settings per defaults for tests
update_module_store_settings(
    MODULESTORE,
    module_store_options={
        'default_class': 'xmodule.hidden_module.HiddenDescriptor',
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
}

############################### BLOCKSTORE #####################################
# Blockstore tests
RUN_BLOCKSTORE_TESTS = os.environ.get('EDXAPP_RUN_BLOCKSTORE_TESTS', 'no').lower() in ('true', 'yes', '1')
BLOCKSTORE_API_URL = os.environ.get('EDXAPP_BLOCKSTORE_API_URL', "http://edx.devstack.blockstore-test:18251/api/v1/")
BLOCKSTORE_API_AUTH_TOKEN = os.environ.get('EDXAPP_BLOCKSTORE_API_AUTH_TOKEN', 'edxapp-test-key')

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

############################# TEMPLATE CONFIGURATION #############################
# Adds mako template dirs for content_libraries tests
MAKO_TEMPLATE_DIRS_BASE.append(
    COMMON_ROOT / 'lib' / 'capa' / 'capa' / 'templates'
)

########################## AUTHOR PERMISSION #######################
FEATURES['ENABLE_CREATOR_GROUP'] = False

# teams feature
FEATURES['ENABLE_TEAMS'] = True

# Dummy secret key for dev/test
SECRET_KEY = '85920908f28904ed733fe576320db18cabd7b6cd'

######### custom courses #########
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



# Lastly, see if the developer has any local overrides.
try:
    from .private import *      # pylint: disable=wildcard-import
except ImportError:
    pass
