"""
This config file extends the test environment configuration
so that we can run the lettuce acceptance tests.
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=W0401, W0614

from .test import *
from .sauce import *

# You need to start the server in debug mode,
# otherwise the browser will not render the pages correctly
DEBUG = True
SITE_NAME = 'localhost:{}'.format(LETTUCE_SERVER_PORT)

# Output Django logs to a file
import logging
logging.basicConfig(filename=TEST_ROOT / "log" / "lms_acceptance.log", level=logging.ERROR)

import os
from random import choice
import string


def seed():
    return os.getppid()

# Silence noisy logs
LOG_OVERRIDES = [
    ('track.middleware', logging.CRITICAL),
    ('codejail.safe_exec', logging.ERROR),
    ('edx.courseware', logging.ERROR),
    ('audit', logging.ERROR),
    ('instructor_task.api_helper', logging.ERROR),
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
        'fs_root': TEST_ROOT / "data",
    }
)
CONTENTSTORE = {
    'ENGINE': 'xmodule.contentstore.mongo.MongoContentStore',
    'DOC_STORE_CONFIG': {
        'host': 'localhost',
        'db': 'acceptance_xcontent_%s' % seed(),
    }
}

# Set this up so that 'paver lms --settings=acceptance' and running the
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

TRACKING_BACKENDS.update({
    'mongo': {
        'ENGINE': 'track.backends.mongodb.MongoBackend'
    }
})

EVENT_TRACKING_BACKENDS.update({
    'mongo': {
        'ENGINE': 'eventtracking.backends.mongodb.MongoBackend',
        'OPTIONS': {
            'database': 'track'
        }
    }
})


BULK_EMAIL_DEFAULT_FROM_EMAIL = "test@test.org"

# Forums are disabled in test.py to speed up unit tests, but we do not have
# per-test control for lettuce acceptance tests.
# If you are writing an acceptance test that needs the discussion service enabled,
# do not write it in lettuce, but instead write it using bok-choy.
# DO NOT CHANGE THIS SETTING HERE.
FEATURES['ENABLE_DISCUSSION_SERVICE'] = False

# Use the auto_auth workflow for creating users and logging them in
FEATURES['AUTOMATIC_AUTH_FOR_TESTING'] = True

# Third-party auth is enabled in lms/envs/test.py for unittests, but we don't
# yet want it for acceptance tests.
FEATURES['ENABLE_THIRD_PARTY_AUTH'] = False

# Enable fake payment processing page
FEATURES['ENABLE_PAYMENT_FAKE'] = True

# Enable email on the instructor dash
FEATURES['ENABLE_INSTRUCTOR_EMAIL'] = True
FEATURES['REQUIRE_COURSE_EMAIL_AUTH'] = False

# Don't actually send any requests to Software Secure for student identity
# verification.
FEATURES['AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING'] = True

# Configure the payment processor to use the fake processing page
# Since both the fake payment page and the shoppingcart app are using
# the same settings, we can generate this randomly and guarantee
# that they are using the same secret.
RANDOM_SHARED_SECRET = ''.join(
    choice(string.letters + string.digits + string.punctuation)
    for x in range(250)
)

CC_PROCESSOR['CyberSource']['SHARED_SECRET'] = RANDOM_SHARED_SECRET
CC_PROCESSOR['CyberSource']['MERCHANT_ID'] = "edx"
CC_PROCESSOR['CyberSource']['SERIAL_NUMBER'] = "0123456789012345678901"
CC_PROCESSOR['CyberSource']['PURCHASE_ENDPOINT'] = "/shoppingcart/payment_fake"

# HACK
# Setting this flag to false causes imports to not load correctly in the lettuce python files
# We do not yet understand why this occurs. Setting this to true is a stopgap measure
USE_I18N = True

FEATURES['ENABLE_FEEDBACK_SUBMISSION'] = False

# Include the lettuce app for acceptance testing, including the 'harvest' django-admin command
INSTALLED_APPS += ('lettuce.django',)
LETTUCE_APPS = ('courseware', 'instructor',)

# Lettuce appears to have a bug that causes it to search
# `instructor_task` when we specify the `instructor` app.
# This causes some pretty cryptic errors as lettuce tries
# to parse files in `instructor_task` as features.
# As a quick workaround, explicitly exclude the `instructor_task` app.
LETTUCE_AVOID_APPS = ('instructor_task',)

LETTUCE_BROWSER = os.environ.get('LETTUCE_BROWSER', 'chrome')

# Where to run: local, saucelabs, or grid
LETTUCE_SELENIUM_CLIENT = os.environ.get('LETTUCE_SELENIUM_CLIENT', 'local')

SELENIUM_GRID = {
    'URL': 'http://127.0.0.1:4444/wd/hub',
    'BROWSER': LETTUCE_BROWSER,
}


#####################################################################
# See if the developer has any local overrides.
try:
    from .private import *  # pylint: disable=F0401
except ImportError:
    pass

# Because an override for where to run will affect which ports to use,
# set these up after the local overrides.
# Configure XQueue interface to use our stub XQueue server
XQUEUE_INTERFACE = {
    "url": "http://127.0.0.1:{0:d}".format(XQUEUE_PORT),
    "django_auth": {
        "username": "lms",
        "password": "***REMOVED***"
    },
    "basic_auth": ('anant', 'agarwal'),
}

# Point the URL used to test YouTube availability to our stub YouTube server
YOUTUBE['API'] = "127.0.0.1:{0}/get_youtube_api/".format(YOUTUBE_PORT)
YOUTUBE['TEST_URL'] = "127.0.0.1:{0}/test_youtube/".format(YOUTUBE_PORT)
YOUTUBE['TEXT_API']['url'] = "127.0.0.1:{0}/test_transcripts_youtube/".format(YOUTUBE_PORT)
