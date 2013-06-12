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

MODULESTORE_OPTIONS = {
    'default_class': 'xmodule.raw_module.RawDescriptor',
    'host': 'localhost',
    'db': 'test_xmodule',
    'collection': 'acceptance_modulestore',
    'fs_root': TEST_ROOT / "data",
    'render_template': 'mitxmako.shortcuts.render_to_string'
}

MODULESTORE = {
    'default': {
        'ENGINE': 'xmodule.modulestore.mongo.DraftMongoModuleStore',
        'OPTIONS': MODULESTORE_OPTIONS
    },
    'direct': {
        'ENGINE': 'xmodule.modulestore.mongo.MongoModuleStore',
        'OPTIONS': MODULESTORE_OPTIONS
    },
    'draft': {
        'ENGINE': 'xmodule.modulestore.mongo.DraftMongoModuleStore',
        'OPTIONS': MODULESTORE_OPTIONS
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

# Include the lettuce app for acceptance testing, including the 'harvest' django-admin command
INSTALLED_APPS += ('lettuce.django',)
LETTUCE_APPS = ('contentstore',)
LETTUCE_SERVER_PORT = 8001
LETTUCE_BROWSER = 'chrome'
