from .aws import *  # pylint: disable=wildcard-import, unused-wildcard-import
import urlparse


FEATURES['CUSTOM_COURSES_EDX'] = True
LABSTER_FEATURES = {
    "ENABLE_WIKI": True,
}

ENV_LABSTER_FEATURES = ENV_TOKENS.get('LABSTER_FEATURES', LABSTER_FEATURES)
for feature, value in ENV_LABSTER_FEATURES.items():
    FEATURES[feature] = value

INSTALLED_APPS += ('labster_course_license',)

LABSTER_WIKI_LINK = ENV_TOKENS.get('LABSTER_WIKI_LINK', 'http://wiki.labster.com/')
LABSTER_API_AUTH_TOKEN = AUTH_TOKENS.get('LABSTER_API_AUTH_TOKEN', '')

LABSTER_API_URL = ENV_TOKENS.get('LABSTER_API_URL', '')
LABSTER_ENDPOINTS = {
    'available_simulations': '',
    'consumer_secret': '',
}

ENV_LABSTER_ENDPOINTS = ENV_TOKENS.get('LABSTER_ENDPOINTS', LABSTER_ENDPOINTS)
for endpoint, value in ENV_LABSTER_ENDPOINTS.items():
    LABSTER_ENDPOINTS[endpoint] = value

LABSTER_DEFAULT_LTI_ID = ENV_TOKENS.get('LABSTER_DEFAULT_LTI_ID', 'MC')
