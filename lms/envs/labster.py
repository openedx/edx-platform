from .aws import *  # pylint: disable=wildcard-import, unused-wildcard-import
import urlparse


LABSTER_SETTINGS = ENV_TOKENS.get('LABSTER_SETTINGS', {})
LABSTER_AUTH = AUTH_TOKENS.get('LABSTER_AUTH', {})

FEATURES['CUSTOM_COURSES_EDX'] = True
FEATURES['SHOW_LABSTER_NOTIFICATION'] = False
LABSTER_FEATURES = {
    "ENABLE_WIKI": True,
    "ENABLE_VOUCHERS": True,
}


ENV_LABSTER_FEATURES = LABSTER_SETTINGS.get('LABSTER_FEATURES', LABSTER_FEATURES)
for feature, value in ENV_LABSTER_FEATURES.items():
    LABSTER_FEATURES[feature] = value

INSTALLED_APPS += (
    'labster_course_license',
    'labster_vouchers',
)

LABSTER_WIKI_LINK = LABSTER_SETTINGS.get('LABSTER_WIKI_LINK', 'https://theory.labster.com/')
LABSTER_API_AUTH_TOKEN = LABSTER_AUTH.get('LABSTER_API_AUTH_TOKEN', '')

LABSTER_API_URL = LABSTER_SETTINGS.get('LABSTER_API_URL', '')
LABSTER_ENDPOINTS = {
    'available_simulations': '',
    'consumer_secret': '',
    'voucher_license': '',
    'voucher_activate': '',
}

ENV_LABSTER_ENDPOINTS = LABSTER_SETTINGS.get('LABSTER_ENDPOINTS', LABSTER_ENDPOINTS)
for endpoint, value in ENV_LABSTER_ENDPOINTS.items():
    LABSTER_ENDPOINTS[endpoint] = value

DISABLE_PROGRESS_TAB = LABSTER_SETTINGS.get('DISABLE_PROGRESS_TAB', True)
LABSTER_DEFAULT_LTI_ID = LABSTER_SETTINGS.get('LABSTER_DEFAULT_LTI_ID', 'MC')

# Sentry integration config
RAVEN_CONFIG = AUTH_TOKENS.get('RAVEN_CONFIG', {})
if RAVEN_CONFIG.get('dsn'):
    INSTALLED_APPS += ('raven.contrib.django.raven_compat',)
