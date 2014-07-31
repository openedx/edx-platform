"""
This config file extends the test environment configuration
so that we can run the lettuce acceptance tests.
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=W0401, W0614

from .test import *
from lms.envs.sauce import *

# You need to start the server in debug mode,
# otherwise the browser will not render the pages correctly
DEBUG = True

# Output Django logs to a file
import logging
logging.basicConfig(filename=TEST_ROOT / "log" / "cms_acceptance.log", level=logging.ERROR)

import os


def seed():
    return os.getppid()

# Silence noisy logs
LOG_OVERRIDES = [
    ('track.middleware', logging.CRITICAL),
    ('codejail.safe_exec', logging.ERROR),
    ('edx.courseware', logging.ERROR),
    ('edxmako.shortcuts', logging.ERROR),
    ('audit', logging.ERROR),
    ('contentstore.views.import_export', logging.CRITICAL),
    ('xmodule.x_module', logging.CRITICAL),
]

for log_name, log_level in LOG_OVERRIDES:
    logging.getLogger(log_name).setLevel(log_level)

update_module_store_settings(
    MODULESTORE,
    doc_store_settings={
        'db': 'acceptance_xmodule',
        'collection': 'acceptance_modulestore_%s' % seed(),
    },
    module_store_options={
        'default_class': 'xmodule.raw_module.RawDescriptor',
        'fs_root': TEST_ROOT / "data",
    }
)

CONTENTSTORE = {
    'ENGINE': 'xmodule.contentstore.mongo.MongoContentStore',
    'DOC_STORE_CONFIG': {
        'host': 'localhost',
        'db': 'acceptance_xcontent_%s' % seed(),
    },
    # allow for additional options that can be keyed on a name, e.g. 'trashcan'
    'ADDITIONAL_OPTIONS': {
        'trashcan': {
            'bucket': 'trash_fs'
        }
    }
}

# Set this up so that 'paver cms --settings=acceptance' and running the
# harvest command both use the same (test) database
# which they can flush without messing up your dev db
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': TEST_ROOT / "db" / "test_edx.db",
        'TEST_NAME': TEST_ROOT / "db" / "test_edx.db",
        'OPTIONS': {
            'timeout': 30,
        },
    }
}

# Use the auto_auth workflow for creating users and logging them in
FEATURES['AUTOMATIC_AUTH_FOR_TESTING'] = True

# Forums are disabled in test.py to speed up unit tests, but we do not have
# per-test control for lettuce acceptance tests.
# If you are writing an acceptance test that needs the discussion service enabled,
# do not write it in lettuce, but instead write it using bok-choy.
# DO NOT CHANGE THIS SETTING HERE.
FEATURES['ENABLE_DISCUSSION_SERVICE'] = False

# HACK
# Setting this flag to false causes imports to not load correctly in the lettuce python files
# We do not yet understand why this occurs. Setting this to true is a stopgap measure
USE_I18N = True

# Include the lettuce app for acceptance testing, including the 'harvest' django-admin command
INSTALLED_APPS += ('lettuce.django',)
LETTUCE_APPS = ('contentstore',)
LETTUCE_BROWSER = os.environ.get('LETTUCE_BROWSER', 'chrome')

# Where to run: local, saucelabs, or grid
LETTUCE_SELENIUM_CLIENT = os.environ.get('LETTUCE_SELENIUM_CLIENT', 'local')

SELENIUM_GRID = {
    'URL': 'http://127.0.0.1:4444/wd/hub',
    'BROWSER': LETTUCE_BROWSER,
}

#####################################################################
# Lastly, see if the developer has any local overrides.
try:
    from .private import *  # pylint: disable=F0401
except ImportError:
    pass

# Point the URL used to test YouTube availability to our stub YouTube server
YOUTUBE['API'] = "127.0.0.1:{0}/get_youtube_api/".format(YOUTUBE_PORT)
YOUTUBE['TEST_URL'] = "127.0.0.1:{0}/test_youtube/".format(YOUTUBE_PORT)
YOUTUBE['TEXT_API']['url'] = "127.0.0.1:{0}/test_transcripts_youtube/".format(YOUTUBE_PORT)
