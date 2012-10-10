"""
This config file runs the simplest dev environment using sqlite, and db-based
sessions. Assumes structure:

/envroot/
        /db   # This is where it'll write the database file
        /mitx # The location of this repo
        /log  # Where we're going to write log files
"""
from .common import *
import os
from path import path


# Nose Test Runner
INSTALLED_APPS += ('django_nose',)
NOSE_ARGS = ['--cover-erase', '--with-xunit', '--with-xcoverage', '--cover-html', '--cover-inclusive']
for app in os.listdir(PROJECT_ROOT / 'djangoapps'):
    NOSE_ARGS += ['--cover-package', app]
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

TEST_ROOT = path('test_root')

# Want static files in the same dir for running on jenkins.
STATIC_ROOT = TEST_ROOT / "staticfiles"

GITHUB_REPO_ROOT = TEST_ROOT / "data"
COMMON_TEST_DATA_ROOT = COMMON_ROOT / "test" / "data"

# TODO (cpennington): We need to figure out how envs/test.py can inject things into common.py so that we don't have to repeat this sort of thing
STATICFILES_DIRS = [
    COMMON_ROOT / "static",
    PROJECT_ROOT / "static",
]
STATICFILES_DIRS += [
    (course_dir, COMMON_TEST_DATA_ROOT / course_dir)
    for course_dir in os.listdir(COMMON_TEST_DATA_ROOT)
    if os.path.isdir(COMMON_TEST_DATA_ROOT / course_dir)
]

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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ENV_ROOT / "db" / "cms.db",
    },

    # The following are for testing purposes...
    'edX/toy/2012_Fall': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ENV_ROOT / "db" / "course1.db",
    },
    
    'edx/full/6.002_Spring_2012': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ENV_ROOT / "db" / "course2.db",
    }
}

CACHES = {
    # This is the cache used for most things. Askbot will not work without a 
    # functioning cache -- it relies on caching to load its settings in places.
    # In staging/prod envs, the sessions also live here.
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'mitx_loc_mem_cache',
        'KEY_FUNCTION': 'util.memcache.safe_key',
    },

    # The general cache is what you get if you use our util.cache. It's used for
    # things like caching the course.xml file for different A/B test groups.
    # We set it to be a DummyCache to force reloading of course.xml in dev.
    # In staging environments, we would grab VERSION from data uploaded by the
    # push process.
    'general': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        'KEY_PREFIX': 'general',
        'VERSION': 4,
        'KEY_FUNCTION': 'util.memcache.safe_key',
    }
}
