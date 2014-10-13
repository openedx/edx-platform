"""
Settings for bok choy tests
"""

import os
from path import path


CONFIG_ROOT = path(__file__).abspath().dirname()  # pylint: disable=E1120
TEST_ROOT = CONFIG_ROOT.dirname().dirname() / "test_root"

########################## Prod-like settings ###################################
# These should be as close as possible to the settings we use in production.
# As in prod, we read in environment and auth variables from JSON files.
# Unlike in prod, we use the JSON files stored in this repo.
# This is a convenience for ensuring (a) that we can consistently find the files
# and (b) that the files are the same in Jenkins as in local dev.
os.environ['SERVICE_VARIANT'] = 'bok_choy'
os.environ['CONFIG_ROOT'] = CONFIG_ROOT

from .aws import *  # pylint: disable=W0401, W0614


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
        'fs_root': (TEST_ROOT / "data").abspath(),  # pylint: disable=E1120
    },
    xml_store_options={
        'data_dir': (TEST_ROOT / "data").abspath(),
    },
    default_store=os.environ.get('DEFAULT_STORE', 'draft'),
)

# Configure the LMS to use our stub XQueue implementation
XQUEUE_INTERFACE['url'] = 'http://localhost:8040'

# Configure the LMS to use our stub ORA implementation
OPEN_ENDED_GRADING_INTERFACE['url'] = 'http://localhost:8041/'

# Enable django-pipeline and staticfiles
STATIC_ROOT = (TEST_ROOT / "staticfiles").abspath()

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

# Unfortunately, we need to use debug mode to serve staticfiles
DEBUG = True

# Point the URL used to test YouTube availability to our stub YouTube server
YOUTUBE_PORT = 9080
YOUTUBE['API'] = "127.0.0.1:{0}/get_youtube_api/".format(YOUTUBE_PORT)
YOUTUBE['TEST_URL'] = "127.0.0.1:{0}/test_youtube/".format(YOUTUBE_PORT)
YOUTUBE['TEXT_API']['url'] = "127.0.0.1:{0}/test_transcripts_youtube/".format(YOUTUBE_PORT)

#####################################################################
# Lastly, see if the developer has any local overrides.
try:
    from .private import *      # pylint: disable=F0401
except ImportError:
    pass
