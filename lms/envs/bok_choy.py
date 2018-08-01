"""
Settings for Bok Choy tests that are used when running LMS.

Bok Choy uses two different settings files:
1. test_static_optimized is used when invoking collectstatic
2. bok_choy is used when running the tests

Note: it isn't possible to have a single settings file, because Django doesn't
support both generating static assets to a directory and also serving static
from the same directory.
"""

import os
from path import Path as path
from tempfile import mkdtemp

from openedx.core.release import RELEASE_LINE

CONFIG_ROOT = path(__file__).abspath().dirname()
TEST_ROOT = CONFIG_ROOT.dirname().dirname() / "test_root"

########################## Prod-like settings ###################################
# These should be as close as possible to the settings we use in production.
# As in prod, we read in environment and auth variables from JSON files.
# Unlike in prod, we use the JSON files stored in this repo.
# This is a convenience for ensuring (a) that we can consistently find the files
# and (b) that the files are the same in Jenkins as in local dev.
os.environ['SERVICE_VARIANT'] = 'bok_choy_docker' if 'BOK_CHOY_HOSTNAME' in os.environ else 'bok_choy'
os.environ['CONFIG_ROOT'] = CONFIG_ROOT

from .aws import *  # pylint: disable=wildcard-import, unused-wildcard-import


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

# Capture the console log via template includes, until webdriver supports log capture again
CAPTURE_CONSOLE_LOG = True

############################ STATIC FILES #############################

# Enable debug so that static assets are served by Django
DEBUG = True

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
PIPELINE_JS_COMPRESSOR = None

################################# CELERY ######################################

CELERY_ALWAYS_EAGER = True
CELERY_RESULT_BACKEND = 'djcelery.backends.cache:CacheBackend'

BLOCK_STRUCTURES_SETTINGS = dict(
    # We have CELERY_ALWAYS_EAGER set to True, so there's no asynchronous
    # code running and the celery routing is unimportant.
    # It does not make sense to retry.
    TASK_MAX_RETRIES=0,
    # course publish task delay is irrelevant is because the task is run synchronously
    COURSE_PUBLISH_TASK_DELAY=0,
    # retry delay is irrelevent because we never retry
    TASK_DEFAULT_RETRY_DELAY=0,
)

###################### Grades ######################
GRADES_DOWNLOAD = {
    'STORAGE_TYPE': 'localfs',
    'BUCKET': 'edx-grades',
    'ROOT_PATH': os.path.join(mkdtemp(), 'edx-s3', 'grades'),
}

FEATURES['PERSISTENT_GRADES_ENABLED_FOR_ALL_TESTS'] = True
FEATURES['ASSUME_ZERO_GRADE_IF_ABSENT_FOR_ALL_TESTS'] = True


# Configure the LMS to use our stub XQueue implementation
XQUEUE_INTERFACE['url'] = 'http://localhost:8040'

# Configure the LMS to use our stub EdxNotes implementation
EDXNOTES_PUBLIC_API = 'http://localhost:8042/api/v1'
EDXNOTES_INTERNAL_API = 'http://localhost:8042/api/v1'


EDXNOTES_CONNECT_TIMEOUT = 10  # time in seconds
EDXNOTES_READ_TIMEOUT = 10  # time in seconds


NOTES_DISABLED_TABS = []

# Silence noisy logs
import logging
LOG_OVERRIDES = [
    ('track.middleware', logging.CRITICAL),
    ('edxmako.shortcuts', logging.ERROR),
    ('dd.dogapi', logging.ERROR),
    ('edx.discussion', logging.CRITICAL),
]
for log_name, log_level in LOG_OVERRIDES:
    logging.getLogger(log_name).setLevel(log_level)

# Enable milestones app
FEATURES['MILESTONES_APP'] = True

# Enable oauth authentication, which we test.
FEATURES['ENABLE_OAUTH2_PROVIDER'] = True

# Enable pre-requisite course
FEATURES['ENABLE_PREREQUISITE_COURSES'] = True

# Enable Course Discovery
FEATURES['ENABLE_COURSE_DISCOVERY'] = True

# Enable student notes
FEATURES['ENABLE_EDXNOTES'] = True

# Enable teams feature
FEATURES['ENABLE_TEAMS'] = True

# Enable custom content licensing
FEATURES['LICENSING'] = True

# Use the auto_auth workflow for creating users and logging them in
FEATURES['AUTOMATIC_AUTH_FOR_TESTING'] = True
FEATURES['RESTRICT_AUTOMATIC_AUTH'] = False

# Open up endpoint for faking Software Secure responses
FEATURES['ENABLE_SOFTWARE_SECURE_FAKE'] = True

FEATURES['ENABLE_ENROLLMENT_TRACK_USER_PARTITION'] = True

########################### Entrance Exams #################################
FEATURES['ENTRANCE_EXAMS'] = True

FEATURES['ENABLE_SPECIAL_EXAMS'] = True


YOUTUBE_HOSTNAME = os.environ.get('BOK_CHOY_HOSTNAME', '127.0.0.1')
# Point the URL used to test YouTube availability to our stub YouTube server
YOUTUBE_PORT = 9080
YOUTUBE['TEST_TIMEOUT'] = 5000
YOUTUBE['API'] = "http://{0}:{1}/get_youtube_api/".format(YOUTUBE_HOSTNAME, YOUTUBE_PORT)
YOUTUBE['METADATA_URL'] = "http://{0}:{1}/test_youtube/".format(YOUTUBE_HOSTNAME, YOUTUBE_PORT)
YOUTUBE['TEXT_API']['url'] = "{0}:{1}/test_transcripts_youtube/".format(YOUTUBE_HOSTNAME, YOUTUBE_PORT)

############################# SECURITY SETTINGS ################################
# Default to advanced security in common.py, so tests can reset here to use
# a simpler security model
FEATURES['ENFORCE_PASSWORD_POLICY'] = False
FEATURES['ENABLE_MAX_FAILED_LOGIN_ATTEMPTS'] = False
FEATURES['SQUELCH_PII_IN_LOGS'] = False
FEATURES['PREVENT_CONCURRENT_LOGINS'] = False
FEATURES['ADVANCED_SECURITY'] = False

FEATURES['ENABLE_MOBILE_REST_API'] = True  # Show video bumper in LMS
FEATURES['ENABLE_VIDEO_BUMPER'] = True  # Show video bumper in LMS
FEATURES['SHOW_BUMPER_PERIODICITY'] = 1

PASSWORD_MIN_LENGTH = None
PASSWORD_COMPLEXITY = {}

# Enable courseware search for tests
FEATURES['ENABLE_COURSEWARE_SEARCH'] = True

# Enable dashboard search for tests
FEATURES['ENABLE_DASHBOARD_SEARCH'] = True

# discussion home panel, which includes a subscription on/off setting for discussion digest emails.
FEATURES['ENABLE_DISCUSSION_HOME_PANEL'] = True

# Enable support for OpenBadges accomplishments
FEATURES['ENABLE_OPENBADGES'] = True

# Use MockSearchEngine as the search engine for test scenario
SEARCH_ENGINE = "search.tests.mock_search_engine.MockSearchEngine"
# Path at which to store the mock index
MOCK_SEARCH_BACKING_FILE = (
    TEST_ROOT / "index_file.dat"
).abspath()

# Verify student settings
VERIFY_STUDENT["SOFTWARE_SECURE"] = {
    "API_ACCESS_KEY": "BBBBBBBBBBBBBBBBBBBB",
    "API_SECRET_KEY": "CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
}

# this secret key should be the same as cms/envs/bok_choy.py's
SECRET_KEY = "very_secret_bok_choy_key"

# Set dummy values for profile image settings.
PROFILE_IMAGE_BACKEND = {
    'class': 'storages.backends.overwrite.OverwriteStorage',
    'options': {
        'location': os.path.join(MEDIA_ROOT, 'profile-images/'),
        'base_url': os.path.join(MEDIA_URL, 'profile-images/'),
    },
}

# Make sure we test with the extended history table
FEATURES['ENABLE_CSMH_EXTENDED'] = True
INSTALLED_APPS.append('coursewarehistoryextended')

BADGING_BACKEND = 'lms.djangoapps.badges.backends.tests.dummy_backend.DummyBackend'

# Configure the LMS to use our stub eCommerce implementation
ECOMMERCE_API_URL = 'http://localhost:8043/api/v2/'

LMS_ROOT_URL = "http://localhost:8000"
if RELEASE_LINE == "master":
    # On master, acceptance tests use edX books, not the default Open edX books.
    HELP_TOKENS_BOOKS = {
        'learner': 'http://edx.readthedocs.io/projects/edx-guide-for-students',
        'course_author': 'http://edx.readthedocs.io/projects/edx-partner-course-staff',
    }

WAFFLE_OVERRIDE = True

############## Settings for Completion API #########################

COMPLETION_BY_VIEWING_DELAY_MS = 1000

################################ JWTs ##############################

JWT_AUTH.update({
    "JWT_PRIVATE_SIGNING_JWK": (
        '{"e": "AQAB", "d": "ZyqyRf6fprfbj3i3a6Ot4VlxWGyj7C4hL_CC_mFYKVSkSE6vDnuoWkK6sxqpORQZL0ObiTRr5srRFFGs-9RKw5jBzf'
        'ssRFR65OAw7uAk0PxCIEeP6TTyFS1tvTA02UXQ_VLsnhi4wA2ks13yitc99vNcKiQm_KBeqjOodLZoU11KhtZhh_W_Z0H24T0FYlBAh6XviGBH'
        'HNUOwJdhOrNZteb6S342yQVgDpeHyuNt1LnveVCk9HHVhdzDYNO-kXJyXrehsfyRhlR60N0KbPw2YuAHa_oUuedBlq9rknj5k2EJtLJ7wU5OHb'
        'GXX04x7RjtKI-tRevnZJA0z5xSnZU3LQ", "n": "4xy0DeL9_IfD51Kqq3M2DMxa-j4mF7DmXvUb0BsXhSSJ4urhIFWjHsf_dyXt4SHGeZtfF'
        'Uc0tcqfyjpFLPZ9fGdSY-Mb7hGUGfG7gAC4PLgQpwsztXP5dzoSy1wrgc4aAUNpipuXUi5Lp7W4VUjAS4vIr6pczL1Le9ExKyuyXYCUUj72Hsw'
        'i7g9sGZe6ADyP5pPdUsgSMQQ7kjaZ0ApBT7YDwADB7_HiA_jAEPqmK9cuFQX1dystT-bjGIcZDfKLyZQAKcKJOwXHeRi0SySHqqQkBCbrfK-8o'
        'ZCnD26p_JX4VUINjeqjtPLMl1M4zHhf_C7BUJj_kcfuc58c3DYprw", "q": "-seCXWembdEd_GwksIhWdyNE7KlPtbbRZX0MV6_eCBNGRNxW'
        'QtYFGvFt2OEs6LQnrAeyA5GiCibdeL-RgYbApn0RSdwAaVjaFf1dtruNA2XgNwyMIYAnqF_ChP7ASQSrYgIBJRtk91IrOTAAWEkti1zvu-oBqv'
        'dfoTR7B6Pzvis", "p": "59cQMakh9IOpI1MBNIM9aMHO4E3FU-YV_5beY8yTZGoUOTvG2p6hIFB5AUgNIGlzpdkYijZGTQ2ynkBAxl7B5wI5'
        'CjnOW1AWvp2S0BsSmNDBYLT7o5zvceOX3KDSzeG8_nRFxFQde5yW9LDLRFZlyEPmMHkOZCIpLCMnatrZRI0", "kid": "bokchoy-tests", '
        '"kty": "RSA"}'
    ),
    "JWT_PUBLIC_SIGNING_JWK_SET": (
        '{"keys": [{"kid": "bokchoy-tests", "e": "AQAB", "kty": "RSA", "n": "4xy0DeL9_IfD51Kqq3M2DMxa-j4mF7DmXvUb0BsXhS'
        'SJ4urhIFWjHsf_dyXt4SHGeZtfFUc0tcqfyjpFLPZ9fGdSY-Mb7hGUGfG7gAC4PLgQpwsztXP5dzoSy1wrgc4aAUNpipuXUi5Lp7W4VUjAS4vI'
        'r6pczL1Le9ExKyuyXYCUUj72Hswi7g9sGZe6ADyP5pPdUsgSMQQ7kjaZ0ApBT7YDwADB7_HiA_jAEPqmK9cuFQX1dystT-bjGIcZDfKLyZQAKc'
        'KJOwXHeRi0SySHqqQkBCbrfK-8oZCnD26p_JX4VUINjeqjtPLMl1M4zHhf_C7BUJj_kcfuc58c3DYprw"}]}'
    ),
})

#####################################################################
# Lastly, see if the developer has any local overrides.
try:
    from .private import *      # pylint: disable=import-error
except ImportError:
    pass
