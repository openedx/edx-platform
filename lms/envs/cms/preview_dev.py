"""
Settings for the LMS that runs alongside the CMS on AWS
"""

from .dev import *

MODULESTORE = {
    'default': {
        'ENGINE': 'xmodule.modulestore.mongo.DraftMongoModuleStore',
        'OPTIONS': modulestore_options
    },
}
