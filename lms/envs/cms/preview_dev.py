"""
Settings for the LMS that runs alongside the CMS on AWS
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=W0401, W0614

from .dev import *

MODULESTORE = {
    'default': {
        'ENGINE': 'xmodule.modulestore.draft.DraftModuleStore',
        'DOC_STORE_CONFIG': DOC_STORE_CONFIG,
        'OPTIONS': modulestore_options
    },
}
