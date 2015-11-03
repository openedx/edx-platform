from .common import *
from lms.envs.common import LABSTER_WIKI_LINK


LABSTER_FEATURES = {
    "ENABLE_WIKI": True,
}

INSTALLED_APPS += (
    'rest_framework.authtoken',
    'labster',
)
