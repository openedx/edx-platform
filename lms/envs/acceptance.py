"""
This config file extends the test environment configuration
so that we can run the lettuce acceptance tests.
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=W0401, W0614

from .test import *

# You need to start the server in debug mode,
# otherwise the browser will not render the pages correctly
DEBUG = True

# Disable warnings for acceptance tests, to make the logs readable
import logging
logging.disable(logging.ERROR)

# Use the mongo store for acceptance tests
modulestore_options = {
    'default_class': 'xmodule.raw_module.RawDescriptor',
    'host': 'localhost',
    'db': 'test_xmodule',
    'collection': 'acceptance_modulestore',
    'fs_root': TEST_ROOT / "data",
    'render_template': 'mitxmako.shortcuts.render_to_string'
}

MODULESTORE = {
    'default': {
        'ENGINE': 'xmodule.modulestore.mongo.MongoModuleStore',
        'OPTIONS': modulestore_options
    },
    'direct': {
        'ENGINE': 'xmodule.modulestore.mongo.MongoModuleStore',
        'OPTIONS': modulestore_options
    }
}

CONTENTSTORE = {
    'ENGINE': 'xmodule.contentstore.mongo.MongoContentStore',
    'OPTIONS': {
        'host': 'localhost',
        'db': 'test_xmodule',
    }
}

# Set this up so that rake lms[acceptance] and running the
# harvest command both use the same (test) database
# which they can flush without messing up your dev db
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': TEST_ROOT / "db" / "test_mitx.db",
        'TEST_NAME': TEST_ROOT / "db" / "test_mitx.db",
    }
}

# Set up XQueue information so that the lms will send
# requests to a mock XQueue server running locally
XQUEUE_PORT = 8027
XQUEUE_INTERFACE = {
    "url": "http://127.0.0.1:%d" % XQUEUE_PORT,
    "django_auth": {
        "username": "lms",
        "password": "***REMOVED***"
    },
    "basic_auth": ('anant', 'agarwal'),
}

# Do not display the YouTube videos in the browser while running the
# acceptance tests. This makes them faster and more reliable
MITX_FEATURES['STUB_VIDEO_FOR_TESTING'] = True

# Include the lettuce app for acceptance testing, including the 'harvest' django-admin command
INSTALLED_APPS += ('lettuce.django',)
LETTUCE_APPS = ('courseware',)
LETTUCE_BROWSER = 'chrome'
