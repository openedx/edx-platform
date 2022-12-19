"""
Settings for Bok Choy tests that are used when running Studio.

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

from django.utils.translation import gettext_lazy
from path import Path as path

from openedx.core.release import RELEASE_LINE
from xmodule.modulestore.modulestore_settings import update_module_store_settings  # lint-amnesty, pylint: disable=wrong-import-order

########################## Prod-like settings ###################################
# These should be as close as possible to the settings we use in production.
# As in prod, we read in environment and auth variables from JSON files.
# Unlike in prod, we use the JSON files stored in this repo.
# This is a convenience for ensuring (a) that we can consistently find the files
# and (b) that the files are the same in Jenkins as in local dev.
os.environ['SERVICE_VARIANT'] = 'bok_choy_docker' if 'BOK_CHOY_HOSTNAME' in os.environ else 'bok_choy'
CONFIG_ROOT = path(__file__).abspath().dirname()
os.environ['STUDIO_CFG'] = str.format("{config_root}/{service_variant}.yml",
                                      config_root=CONFIG_ROOT,
                                      service_variant=os.environ['SERVICE_VARIANT'])
os.environ['REVISION_CFG'] = f"{CONFIG_ROOT}/revisions.yml"

from .production import *  # pylint: disable=wildcard-import, unused-wildcard-import, wrong-import-position


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

# Needed to enable licensing on video blocks
XBLOCK_SETTINGS.update({'VideoBlock': {'licensing_enabled': True}})

# Capture the console log via template includes, until webdriver supports log capture again
CAPTURE_CONSOLE_LOG = True

PLATFORM_NAME = gettext_lazy("édX")
PLATFORM_DESCRIPTION = gettext_lazy("Open édX Platform")
STUDIO_NAME = gettext_lazy("Your Platform 𝓢𝓽𝓾𝓭𝓲𝓸")
STUDIO_SHORT_NAME = gettext_lazy("𝓢𝓽𝓾𝓭𝓲𝓸")

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

LOG_OVERRIDES = [
    ('common.djangoapps.track.middleware', logging.CRITICAL),
    ('edx.discussion', logging.CRITICAL),
]
for log_name, log_level in LOG_OVERRIDES:
    logging.getLogger(log_name).setLevel(log_level)

# Use the auto_auth workflow for creating users and logging them in
FEATURES['AUTOMATIC_AUTH_FOR_TESTING'] = True
FEATURES['RESTRICT_AUTOMATIC_AUTH'] = False

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
YOUTUBE['API'] = f"http://{YOUTUBE_HOSTNAME}:{YOUTUBE_PORT}/get_youtube_api/"
YOUTUBE['METADATA_URL'] = f"http://{YOUTUBE_HOSTNAME}:{YOUTUBE_PORT}/test_youtube/"

FEATURES['ENABLE_COURSEWARE_INDEX'] = True
FEATURES['ENABLE_LIBRARY_INDEX'] = True
FEATURES['ENABLE_CONTENT_LIBRARY_INDEX'] = False

ORGANIZATIONS_AUTOCREATE = False

SEARCH_ENGINE = "search.tests.mock_search_engine.MockSearchEngine"
# Path at which to store the mock index
MOCK_SEARCH_BACKING_FILE = (
    TEST_ROOT / "index_file.dat"
).abspath()

# this secret key should be the same as lms/envs/bok_choy.py's
SECRET_KEY = "very_secret_bok_choy_key"

LMS_ROOT_URL = "http://localhost:8003"
if RELEASE_LINE == "master":
    # On master, acceptance tests use edX books, not the default Open edX books.
    HELP_TOKENS_BOOKS = {
        'learner': 'https://edx.readthedocs.io/projects/edx-guide-for-students',
        'course_author': 'https://edx.readthedocs.io/projects/edx-partner-course-staff',
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

INSTALLED_APPS.append('openedx.testing.coverage_context_listener')

#####################################################################
# Lastly, see if the developer has any local overrides.
try:
    from .private import *      # pylint: disable=wildcard-import
except ImportError:
    pass
