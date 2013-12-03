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

# Output Django logs to a file
import logging
logging.basicConfig(filename=TEST_ROOT / "log" / "lms_acceptance.log", level=logging.ERROR)

import os
from random import choice, randint
import string


def seed():
    return os.getppid()

# Use the mongo store for acceptance tests
DOC_STORE_CONFIG = {
    'host': 'localhost',
    'db': 'acceptance_xmodule',
    'collection': 'acceptance_modulestore_%s' % seed(),
}

modulestore_options = {
    'default_class': 'xmodule.raw_module.RawDescriptor',
    'fs_root': TEST_ROOT / "data",
    'render_template': 'edxmako.shortcuts.render_to_string',
}

MODULESTORE = {
    'default': {
        'ENGINE': 'xmodule.modulestore.mixed.MixedModuleStore',
        'OPTIONS': {
            'mappings': {},
            'stores': {
                'default': {
                    'ENGINE': 'xmodule.modulestore.mongo.MongoModuleStore',
                    'DOC_STORE_CONFIG': DOC_STORE_CONFIG,
                    'OPTIONS': modulestore_options
                }
            }
        }
    }
}

MODULESTORE['direct'] = MODULESTORE['default']

CONTENTSTORE = {
    'ENGINE': 'xmodule.contentstore.mongo.MongoContentStore',
    'DOC_STORE_CONFIG': {
        'host': 'localhost',
        'db': 'acceptance_xcontent_%s' % seed(),
    }
}

# Set this up so that rake lms[acceptance] and running the
# harvest command both use the same (test) database
# which they can flush without messing up your dev db
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': TEST_ROOT / "db" / "test_edx.db",
        'TEST_NAME': TEST_ROOT / "db" / "test_edx.db",
    }
}

TRACKING_BACKENDS.update({
    'mongo': {
        'ENGINE': 'track.backends.mongodb.MongoBackend'
    }
})


# Enable asset pipeline
# Our fork of django-pipeline uses `PIPELINE` instead of `PIPELINE_ENABLED`
# PipelineFinder is explained here: http://django-pipeline.readthedocs.org/en/1.1.24/storages.html
PIPELINE = True
STATICFILES_FINDERS += ('pipeline.finders.PipelineFinder', )

BULK_EMAIL_DEFAULT_FROM_EMAIL = "test@test.org"

# Forums are disabled in test.py to speed up unit tests, but we do not have
# per-test control for acceptance tests
MITX_FEATURES['ENABLE_DISCUSSION_SERVICE'] = True

# Use the auto_auth workflow for creating users and logging them in
MITX_FEATURES['AUTOMATIC_AUTH_FOR_TESTING'] = True

# Enable fake payment processing page
MITX_FEATURES['ENABLE_PAYMENT_FAKE'] = True

# Enable email on the instructor dash
MITX_FEATURES['ENABLE_INSTRUCTOR_EMAIL'] = True
MITX_FEATURES['REQUIRE_COURSE_EMAIL_AUTH'] = False

# Don't actually send any requests to Software Secure for student identity
# verification.
MITX_FEATURES['AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING'] = True

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

MITX_FEATURES['ENABLE_FEEDBACK_SUBMISSION'] = True
FEEDBACK_SUBMISSION_EMAIL = 'dummy@example.com'

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
if LETTUCE_SELENIUM_CLIENT == 'saucelabs':
    LETTUCE_SERVER_PORT = choice(PORTS)
    PORTS.remove(LETTUCE_SERVER_PORT)
else:
    LETTUCE_SERVER_PORT = randint(1024, 65535)

# Set up XQueue information so that the lms will send
# requests to a mock XQueue server running locally
if LETTUCE_SELENIUM_CLIENT == 'saucelabs':
    XQUEUE_PORT = choice(PORTS)
    PORTS.remove(XQUEUE_PORT)
else:
    XQUEUE_PORT = randint(1024, 65535)

XQUEUE_INTERFACE = {
    "url": "http://127.0.0.1:%d" % XQUEUE_PORT,
    "django_auth": {
        "username": "lms",
        "password": "***REMOVED***"
    },
    "basic_auth": ('anant', 'agarwal'),
}

# Set up Video information so that the lms will send
# requests to a mock Youtube server running locally
if LETTUCE_SELENIUM_CLIENT == 'saucelabs':
    VIDEO_PORT = choice(PORTS)
    PORTS.remove(VIDEO_PORT)
else:
    VIDEO_PORT = randint(1024, 65535)
