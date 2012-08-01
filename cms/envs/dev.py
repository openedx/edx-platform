"""
This config file runs the simplest dev environment"""

from .common import *

import logging
import sys
logging.basicConfig(stream=sys.stdout, )

DEBUG = True
TEMPLATE_DEBUG = DEBUG

MODULESTORE = {
    'default': {
        'ENGINE': 'xmodule.modulestore.mongo.MongoModuleStore',
        'OPTIONS': {
            'default_class': 'xmodule.raw_module.RawDescriptor',
            'host': 'localhost',
            'db': 'xmodule',
            'collection': 'modulestore',
            'fs_root': GITHUB_REPO_ROOT,
        }
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ENV_ROOT / "db" / "cms.db",
    }
}

REPOS = {
    'edx4edx': {
        'branch': 'master',
        'origin': 'git@github.com:MITx/edx4edx.git',
    },
    'content-mit-6002x': {
        'branch': 'master',
        #'origin': 'git@github.com:MITx/6002x-fall-2012.git',
        'origin': 'git@github.com:MITx/content-mit-6002x.git',
    },
    '6.00x': {
        'branch': 'master',
        'origin': 'git@github.com:MITx/6.00x.git',
    },
    '7.00x': {
        'branch': 'master',
        'origin': 'git@github.com:MITx/7.00x.git',
    },
    '3.091x': {
        'branch': 'master',
        'origin': 'git@github.com:MITx/3.091x.git',
    },
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

# Make the keyedcache startup warnings go away
CACHE_TIMEOUT = 0
