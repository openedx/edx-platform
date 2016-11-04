from lms.envs.devstack import *


FEATURES.update({
    'ENABLE_COURSEWARE_SEARCH': False,
    'USE_DJANGO_PIPELINE': False,
})
