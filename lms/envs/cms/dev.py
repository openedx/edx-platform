"""
Settings for the LMS that runs alongside the CMS on AWS
"""

from ..dev import *

MODULESTORE = {
    'default': {
        'ENGINE': 'xmodule.modulestore.mongo.MongoModuleStore',
        'OPTIONS': {
            'default_class': 'xmodule.raw_module.RawDescriptor',
            'host': 'localhost',
            'db': 'xmodule',
            'collection': 'modulestore',
            'fs_root': DATA_DIR,
            'render_template': 'mitxmako.shortcuts.render_to_string',
        }
    }
}
