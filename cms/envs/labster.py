from .aws import *  # pylint: disable=wildcard-import, unused-wildcard-import


LABSTER_SETTINGS = ENV_TOKENS.get('LABSTER_SETTINGS', {})
LABSTER_AUTH = AUTH_TOKENS.get('LABSTER_AUTH', {})

FEATURES['CUSTOM_COURSES_EDX'] = True
LABSTER_FEATURES = {
    "ENABLE_WIKI": True,
}

ENV_LABSTER_FEATURES = LABSTER_SETTINGS.get('LABSTER_FEATURES', LABSTER_FEATURES)
for feature, value in ENV_LABSTER_FEATURES.items():
    FEATURES[feature] = value

INSTALLED_APPS += (
    'rest_framework.authtoken',
    'openedx.core.djangoapps.labster.course',
)

LABSTER_WIKI_LINK = LABSTER_SETTINGS.get('LABSTER_WIKI_LINK', 'https://theory.labster.com/')
