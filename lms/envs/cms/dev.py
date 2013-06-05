"""
Settings for the LMS that runs alongside the CMS on AWS
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=W0401, W0614

from ..dev import *

MITX_FEATURES['AUTH_USE_MIT_CERTIFICATES'] = False

SUBDOMAIN_BRANDING['edge'] = 'edge'
SUBDOMAIN_BRANDING['preview.edge'] = 'edge'
VIRTUAL_UNIVERSITIES = ['edge']
META_UNIVERSITIES = {}

modulestore_options = {
    'default_class': 'xmodule.raw_module.RawDescriptor',
    'host': 'localhost',
    'db': 'xmodule',
    'collection': 'modulestore',
    'fs_root': DATA_DIR,
    'render_template': 'mitxmako.shortcuts.render_to_string'
}

MODULESTORE = {
    'default': {
        'ENGINE': 'xmodule.modulestore.mongo.MongoModuleStore',
        'OPTIONS': modulestore_options
    },
}

CONTENTSTORE = {
    'ENGINE': 'xmodule.contentstore.mongo.MongoContentStore',
    'OPTIONS': {
        'host': 'localhost',
        'db': 'xcontent',
    }
}

INSTALLED_APPS += (
    # Mongo perf stats
    'debug_toolbar_mongo',
    )


DEBUG_TOOLBAR_PANELS += (
   'debug_toolbar_mongo.panel.MongoDebugPanel',
   )
