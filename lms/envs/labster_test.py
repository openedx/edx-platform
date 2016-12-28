from .test import *  # pylint: disable=wildcard-import, unused-wildcard-import


LABSTER_FEATURES = {
    "ENABLE_WIKI": False,
    "ENABLE_VOUCHERS": False,
}

LABSTER_APPS = (
    'labster_course_license',
    'labster_vouchers',
)

INSTALLED_APPS += LABSTER_APPS

MIGRATION_MODULES.update({
    app: "app.migrations_not_used_in_tests" for app in LABSTER_APPS
})

FEATURES['SHOW_LABSTER_NOTIFICATION'] = False
LABSTER_WIKI_LINK = 'https://theory.example.com/'

LABSTER_API_AUTH_TOKEN = ''

LABSTER_API_URL = ''
LABSTER_ENDPOINTS = {
    'available_simulations': 'https://example.com/available_simulations',
    'consumer_secret': 'https://example.com/consumer_secret',
    'voucher_license': 'https://example.com/vouchers/{}/license/',
    'voucher_activate': 'https://example.com/voucher/activate/',
}

DISABLE_PROGRESS_TAB = False
LABSTER_DEFAULT_LTI_ID = 'MC'
