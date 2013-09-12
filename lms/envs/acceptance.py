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

# Disable warnings for acceptance tests, to make the logs readable
import logging
logging.disable(logging.ERROR)
import os
from random import choice, randint
import string


def seed():
    return os.getppid()

# Use the mongo store for acceptance tests
modulestore_options = {
    'default_class': 'xmodule.raw_module.RawDescriptor',
    'host': 'localhost',
    'db': 'acceptance_xmodule',
    'collection': 'acceptance_modulestore_%s' % seed(),
    'fs_root': TEST_ROOT / "data",
    'render_template': 'mitxmako.shortcuts.render_to_string',
}

MODULESTORE = {
    'default': {
        'ENGINE': 'xmodule.modulestore.mixed.MixedModuleStore',
        'OPTIONS': {
            'mappings': {},
            'stores': {
                'default': {
                    'ENGINE': 'xmodule.modulestore.mongo.MongoModuleStore',
                    'OPTIONS': modulestore_options
                }
            }
        }
    }
}

MODULESTORE['direct'] = MODULESTORE['default']

CONTENTSTORE = {
    'ENGINE': 'xmodule.contentstore.mongo.MongoContentStore',
    'OPTIONS': {
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

# Set up XQueue information so that the lms will send
# requests to a mock XQueue server running locally
XQUEUE_PORT = choice(PORTS) if SAUCE.get('SAUCE_ENABLED') else randint(1024, 65535)
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
VIDEO_PORT = XQUEUE_PORT + 2

# Forums are disabled in test.py to speed up unit tests, but we do not have
# per-test control for acceptance tests
MITX_FEATURES['ENABLE_DISCUSSION_SERVICE'] = True

# Use the auto_auth workflow for creating users and logging them in
MITX_FEATURES['AUTOMATIC_AUTH_FOR_TESTING'] = True

# Enable fake payment processing page
MITX_FEATURES['ENABLE_PAYMENT_FAKE'] = True

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
LETTUCE_APPS = ('courseware',)
LETTUCE_SERVER_PORT = choice(PORTS) if SAUCE.get('SAUCE_ENABLED') else randint(1024, 65535)
LETTUCE_BROWSER = os.environ.get('LETTUCE_BROWSER', 'chrome')

#####################################################################
# Lastly, see if the developer has any local overrides.
try:
    from .private import *      # pylint: disable=F0401
except ImportError:
    pass
