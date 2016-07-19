from .test import *  # pylint: disable=wildcard-import, unused-wildcard-import
import urlparse


FEATURES['SHOW_LABSTER_NOTIFICATION'] = True
LABSTER_FEATURES = {
    "ENABLE_WIKI": True,
}

INSTALLED_APPS += (
    'labster_course_license',
)

LABSTER_WIKI_LINK = 'https://theory.labster.com/'
LABSTER_API_AUTH_TOKEN = ''

LABSTER_API_URL = ''
LABSTER_ENDPOINTS = {
    'available_simulations': 'https://example.com/available_simulations',
    'consumer_secret': 'https://example.com/consumer_secret',
}

LABSTER_DEFAULT_LTI_ID = 'MC'
