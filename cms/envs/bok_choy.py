"""
Settings for Bok Choy tests that are used when running Studio.

Bok Choy uses two different settings files:
1. test_static_optimized is used when invoking collectstatic
2. bok_choy is used when running the tests

Note: it isn't possible to have a single settings file, because Django doesn't
support both generating static assets to a directory and also serving static
from the same directory.
"""

import os
from path import Path as path

from openedx.core.release import RELEASE_LINE

########################## Prod-like settings ###################################
# These should be as close as possible to the settings we use in production.
# As in prod, we read in environment and auth variables from JSON files.
# Unlike in prod, we use the JSON files stored in this repo.
# This is a convenience for ensuring (a) that we can consistently find the files
# and (b) that the files are the same in Jenkins as in local dev.
os.environ['SERVICE_VARIANT'] = 'bok_choy_docker' if 'BOK_CHOY_HOSTNAME' in os.environ else 'bok_choy'
os.environ['CONFIG_ROOT'] = path(__file__).abspath().dirname()

from .aws import *  # pylint: disable=wildcard-import, unused-wildcard-import

######################### Testing overrides ####################################

# Redirect to the test_root folder within the repo
TEST_ROOT = REPO_ROOT / "test_root"
GITHUB_REPO_ROOT = (TEST_ROOT / "data").abspath()
LOG_DIR = (TEST_ROOT / "log").abspath()
DATA_DIR = TEST_ROOT / "data"

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

# Needed to enable licensing on video modules
XBLOCK_SETTINGS.update({'VideoDescriptor': {'licensing_enabled': True}})

############################ STATIC FILES #############################

# Enable debug so that static assets are served by Django
DEBUG = True

# Serve static files at /static directly from the staticfiles directory under test root
# Note: optimized files for testing are generated with settings from test_static_optimized
STATIC_URL = "/static/"
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
]
STATICFILES_DIRS = [
    (TEST_ROOT / "staticfiles" / "cms").abspath(),
]

DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_ROOT = TEST_ROOT / "uploads"

WEBPACK_LOADER['DEFAULT']['STATS_FILE'] = TEST_ROOT / "staticfiles" / "cms" / "webpack-stats.json"

# Silence noisy logs
import logging
LOG_OVERRIDES = [
    ('track.middleware', logging.CRITICAL),
    ('edx.discussion', logging.CRITICAL),
]
for log_name, log_level in LOG_OVERRIDES:
    logging.getLogger(log_name).setLevel(log_level)

# Use the auto_auth workflow for creating users and logging them in
FEATURES['AUTOMATIC_AUTH_FOR_TESTING'] = True

# Enable milestones app
FEATURES['MILESTONES_APP'] = True

# Enable pre-requisite course
FEATURES['ENABLE_PREREQUISITE_COURSES'] = True

# Enable student notes
FEATURES['ENABLE_EDXNOTES'] = True

# Enable teams feature
FEATURES['ENABLE_TEAMS'] = True

# Enable custom content licensing
FEATURES['LICENSING'] = True

FEATURES['ENABLE_MOBILE_REST_API'] = True  # Enable video bumper in Studio
FEATURES['ENABLE_VIDEO_BUMPER'] = True  # Enable video bumper in Studio settings

FEATURES['ENABLE_ENROLLMENT_TRACK_USER_PARTITION'] = True

# Whether archived courses (courses with end dates in the past) should be
# shown in Studio in a separate list.
FEATURES['ENABLE_SEPARATE_ARCHIVED_COURSES'] = True

# Enable support for OpenBadges accomplishments
FEATURES['ENABLE_OPENBADGES'] = True

# Enable partner support link in Studio footer
PARTNER_SUPPORT_EMAIL = 'partner-support@example.com'

########################### Entrance Exams #################################
FEATURES['ENTRANCE_EXAMS'] = True

FEATURES['ENABLE_SPECIAL_EXAMS'] = True

# Point the URL used to test YouTube availability to our stub YouTube server
YOUTUBE_PORT = 9080
YOUTUBE['TEST_TIMEOUT'] = 5000
YOUTUBE_HOSTNAME = os.environ.get('BOK_CHOY_HOSTNAME', '127.0.0.1')
YOUTUBE['API'] = "http://{0}:{1}/get_youtube_api/".format(YOUTUBE_HOSTNAME, YOUTUBE_PORT)
YOUTUBE['METADATA_URL'] = "http://{0}:{1}/test_youtube/".format(YOUTUBE_HOSTNAME, YOUTUBE_PORT)
YOUTUBE['TEXT_API']['url'] = "{0}:{1}/test_transcripts_youtube/".format(YOUTUBE_HOSTNAME, YOUTUBE_PORT)

FEATURES['ENABLE_COURSEWARE_INDEX'] = True
FEATURES['ENABLE_LIBRARY_INDEX'] = True

FEATURES['ORGANIZATIONS_APP'] = True
SEARCH_ENGINE = "search.tests.mock_search_engine.MockSearchEngine"
# Path at which to store the mock index
MOCK_SEARCH_BACKING_FILE = (
    TEST_ROOT / "index_file.dat"
).abspath()

# this secret key should be the same as lms/envs/bok_choy.py's
SECRET_KEY = "very_secret_bok_choy_key"

LMS_ROOT_URL = "http://localhost:8000"
if RELEASE_LINE == "master":
    # On master, acceptance tests use edX books, not the default Open edX books.
    HELP_TOKENS_BOOKS = {
        'learner': 'http://edx.readthedocs.io/projects/edx-guide-for-students',
        'course_author': 'http://edx.readthedocs.io/projects/edx-partner-course-staff',
    }

########################## VIDEO TRANSCRIPTS STORAGE ############################
VIDEO_TRANSCRIPTS_SETTINGS = dict(
    VIDEO_TRANSCRIPTS_MAX_BYTES=3 * 1024 * 1024,    # 3 MB
    STORAGE_KWARGS=dict(
        location=MEDIA_ROOT,
        base_url=MEDIA_URL,
    ),
    DIRECTORY_PREFIX='video-transcripts/',
)

#####################################################################
# Lastly, see if the developer has any local overrides.
try:
    from .private import *      # pylint: disable=import-error
except ImportError:
    pass
