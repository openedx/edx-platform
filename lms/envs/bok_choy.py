# Settings for bok choy tests

import os
from path import path


CONFIG_ROOT = path(__file__).abspath().dirname()
TEST_ROOT = CONFIG_ROOT.dirname().dirname() / "test_root"

########################## Prod-like settings ###################################
# These should be as close as possible to the settings we use in production.
# As in prod, we read in environment and auth variables from JSON files.
# Unlike in prod, we use the JSON files stored in this repo.
# This is a convenience for ensuring (a) that we can consistently find the files
# and (b) that the files are the same in Jenkins as in local dev.
os.environ['SERVICE_VARIANT'] = 'bok_choy'
os.environ['CONFIG_ROOT'] = CONFIG_ROOT

from aws import * # pylint: disable=W0401, W0614


######################### Testing overrides ####################################

# Needed for the `reset_db` management command
INSTALLED_APPS += ('django_extensions',)

# Redirect to the test_root folder within the repo
GITHUB_REPO_ROOT = (TEST_ROOT / "data").abspath()
LOG_DIR = (TEST_ROOT / "log").abspath()

# Configure Mongo modulestore to use the test folder within the repo
MONGO_MODULESTORE = MODULESTORE['default']['OPTIONS']['stores']['default']
MONGO_MODULESTORE['OPTIONS']['fs_root'] = (TEST_ROOT / "data").abspath()

# Configure XML modulestore to use test root data dir
XML_MODULESTORE = MODULESTORE['default']['OPTIONS']['stores']['xml']
XML_MODULESTORE['OPTIONS']['data_dir'] = (TEST_ROOT / "data").abspath()

# Enable django-pipeline and staticfiles
STATIC_ROOT = (TEST_ROOT / "staticfiles").abspath()
PIPELINE = True

# Silence noisy logs
import logging
LOG_OVERRIDES = [
    ('track.middleware', logging.CRITICAL),
    ('edxmako.shortcuts', logging.ERROR),
    ('dd.dogapi', logging.ERROR)
]
for log_name, log_level in LOG_OVERRIDES:
    logging.getLogger(log_name).setLevel(log_level)

# Unfortunately, we need to use debug mode to serve staticfiles
DEBUG = True
