"""
This config file runs the dev environment, but with mongo as the datastore
"""
from .dev import *

GITHUB_REPO_ROOT = ENV_ROOT / "data"

MODULESTORE = {
    'default': {
        'ENGINE': 'xmodule.modulestore.mongo.MongoModuleStore',
        'OPTIONS': {
            'default_class': 'xmodule.raw_module.RawDescriptor',
            'host': 'localhost',
            'db': 'xmodule',
            'collection': 'modulestore',
            'fs_root': GITHUB_REPO_ROOT,
            'render_template': 'mitxmako.shortcuts.render_to_string',
        }
    }
}
