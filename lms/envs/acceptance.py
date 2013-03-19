"""
This config file extends the test environment configuration
so that we can run the lettuce acceptance tests.
"""
from .test import *

# You need to start the server in debug mode,
# otherwise the browser will not render the pages correctly
DEBUG = True

# Use the mongo store for acceptance tests
modulestore_options = {
    'default_class': 'xmodule.raw_module.RawDescriptor',
    'host': 'localhost',
    'db': 'test_xmodule',
    'collection': 'modulestore',
    'fs_root': GITHUB_REPO_ROOT,
    'render_template': 'mitxmako.shortcuts.render_to_string',
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
        'db': 'test_xcontent',
    }
}

# Set this up so that rake lms[acceptance] and running the
# harvest command both use the same (test) database
# which they can flush without messing up your dev db
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ENV_ROOT / "db" / "test_mitx.db",
        'TEST_NAME': ENV_ROOT / "db" / "test_mitx.db",
    }
}

# Do not display the YouTube videos in the browser while running the
# acceptance tests. This makes them faster and more reliable
MITX_FEATURES['STUB_VIDEO_FOR_TESTING'] = True

# Include the lettuce app for acceptance testing, including the 'harvest' django-admin command
INSTALLED_APPS += ('lettuce.django',)
LETTUCE_APPS = ('courseware',)
