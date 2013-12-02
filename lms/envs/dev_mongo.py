"""
This config file runs the dev environment, but with mongo as the datastore
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=W0401, W0614

from .dev import *

GITHUB_REPO_ROOT = ENV_ROOT / "data"

MODULESTORE = {
    'default': {
        'ENGINE': 'xmodule.modulestore.mongo.MongoModuleStore',
        'DOC_STORE_CONFIG': {
            'host': 'localhost',
            'db': 'xmodule',
            'collection': 'modulestore',
        },
        'OPTIONS': {
            'default_class': 'xmodule.raw_module.RawDescriptor',
            'fs_root': GITHUB_REPO_ROOT,
            'render_template': 'edxmako.shortcuts.render_to_string',
        }
    }
}
