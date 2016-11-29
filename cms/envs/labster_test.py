from .test import *  # pylint: disable=wildcard-import, unused-wildcard-import


LABSTER_FEATURES = {
    "ENABLE_WIKI": False,
}

INSTALLED_APPS += (
    'rest_framework.authtoken',
    'openedx.core.djangoapps.labster.course',
)

LABSTER_WIKI_LINK = 'https://theory.example.com/'
