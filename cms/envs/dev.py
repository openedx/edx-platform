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
            'db': 'mongo_base',
            'collection': 'key_store',
        }
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ENV_ROOT / "db" / "mitx.db",
    }
}

REPO_ROOT = ENV_ROOT / "content"

REPOS = {
    'edx4edx': {
        'path': REPO_ROOT / "edx4edx",
        'org': 'edx',
        'course': 'edx4edx',
        'branch': 'for_cms',
        'origin': 'git@github.com:MITx/edx4edx.git',
    },
    '6002x-fall-2012': {
        'path': REPO_ROOT / '6002x-fall-2012',
        'org': 'mit.edu',
        'course': '6.002x',
        'branch': 'master',
        'origin': 'git@github.com:MITx/6002x-fall-2012.git',
    },
    '6.00x': {
        'path': REPO_ROOT / '6.00x',
        'org': 'mit.edu',
        'course': '6.00x',
        'branch': 'master',
        'origin': 'git@github.com:MITx/6.00x.git',
    },
    '7.00x': {
        'path': REPO_ROOT / '7.00x',
        'org': 'mit.edu',
        'course': '7.00x',
        'branch': 'master',
        'origin': 'git@github.com:MITx/7.00x.git',
    },
    '3.091x': {
        'path': REPO_ROOT / '3.091x',
        'org': 'mit.edu',
        'course': '3.091x',
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
