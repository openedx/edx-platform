"""
Settings for bok choy tests
"""

import os
from path import path
from tempfile import mkdtemp

# Pylint gets confused by path.py instances, which report themselves as class
# objects. As a result, pylint applies the wrong regex in validating names,
# and throws spurious errors. Therefore, we disable invalid-name checking.
# pylint: disable=invalid-name

CONFIG_ROOT = path(__file__).abspath().dirname()  # pylint: disable=no-value-for-parameter
TEST_ROOT = CONFIG_ROOT.dirname().dirname() / "test_root"

########################## Prod-like settings ###################################
# These should be as close as possible to the settings we use in production.
# As in prod, we read in environment and auth variables from JSON files.
# Unlike in prod, we use the JSON files stored in this repo.
# This is a convenience for ensuring (a) that we can consistently find the files
# and (b) that the files are the same in Jenkins as in local dev.
os.environ['SERVICE_VARIANT'] = 'bok_choy'
os.environ['CONFIG_ROOT'] = CONFIG_ROOT

from .aws import *  # pylint: disable=wildcard-import, unused-wildcard-import


######################### Testing overrides ####################################

# Needed for the reset database management command
INSTALLED_APPS += ('django_extensions',)

# Redirect to the test_root folder within the repo
GITHUB_REPO_ROOT = (TEST_ROOT / "data").abspath()
LOG_DIR = (TEST_ROOT / "log").abspath()

# Configure modulestore to use the test folder within the repo
update_module_store_settings(
    MODULESTORE,
    module_store_options={
        'fs_root': (TEST_ROOT / "data").abspath(),  # pylint: disable=no-value-for-parameter
    },
    xml_store_options={
        'data_dir': (TEST_ROOT / "data").abspath(),
    },
    default_store=os.environ.get('DEFAULT_STORE', 'draft'),
)

############################ STATIC FILES #############################
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_ROOT = TEST_ROOT / "uploads"
MEDIA_URL = "/static/uploads/"

################################# CELERY ######################################

CELERY_ALWAYS_EAGER = True
CELERY_RESULT_BACKEND = 'djcelery.backends.cache:CacheBackend'

###################### Grade Downloads ######################
GRADES_DOWNLOAD = {
    'STORAGE_TYPE': 'localfs',
    'BUCKET': 'edx-grades',
    'ROOT_PATH': os.path.join(mkdtemp(), 'edx-s3', 'grades'),
}

# Configure the LMS to use our stub XQueue implementation
XQUEUE_INTERFACE['url'] = 'http://localhost:8040'

# Configure the LMS to use our stub ORA implementation
OPEN_ENDED_GRADING_INTERFACE['url'] = 'http://localhost:8041/'

# Configure the LMS to use our stub EdxNotes implementation
EDXNOTES_PUBLIC_API = 'http://localhost:8042/api/v1'
EDXNOTES_INTERNAL_API = 'http://localhost:8042/api/v1'

# Enable django-pipeline and staticfiles
STATIC_ROOT = (TEST_ROOT / "staticfiles" / "lms").abspath()

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

# Unfortunately, we need to use debug mode to serve staticfiles
DEBUG = True

########################### Entrance Exams #################################
FEATURES['MILESTONES_APP'] = True
FEATURES['ENTRANCE_EXAMS'] = True

# Point the URL used to test YouTube availability to our stub YouTube server
YOUTUBE_PORT = 9080
YOUTUBE['API'] = "http://127.0.0.1:{0}/get_youtube_api/".format(YOUTUBE_PORT)
YOUTUBE['METADATA_URL'] = "http://127.0.0.1:{0}/test_youtube/".format(YOUTUBE_PORT)
YOUTUBE['TEXT_API']['url'] = "127.0.0.1:{0}/test_transcripts_youtube/".format(YOUTUBE_PORT)

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

# Use MockSearchEngine as the search engine for test scenario
SEARCH_ENGINE = "search.tests.mock_search_engine.MockSearchEngine"
# Path at which to store the mock index
MOCK_SEARCH_BACKING_FILE = (
    TEST_ROOT / "index_file.dat"  # pylint: disable=no-value-for-parameter
).abspath()

# Generate a random UUID so that different runs of acceptance tests don't break each other
import uuid
SECRET_KEY = uuid.uuid4().hex

# Set dummy values for profile image settings.
PROFILE_IMAGE_BACKEND = {
    'class': 'storages.backends.overwrite.OverwriteStorage',
    'options': {
        'location': os.path.join(MEDIA_ROOT, 'profile-images/'),
        'base_url': os.path.join(MEDIA_URL, 'profile-images/'),
    },
}
#####################################################################
# Lastly, see if the developer has any local overrides.
try:
    from .private import *      # pylint: disable=import-error
except ImportError:
    pass
