from .aws import *  # pylint: disable=wildcard-import, unused-wildcard-import


FEATURES['CUSTOM_COURSES_EDX'] = True
LABSTER_FEATURES = {
    "ENABLE_WIKI": True,
}

ENV_LABSTER_FEATURES = ENV_TOKENS.get('LABSTER_FEATURES', LABSTER_FEATURES)
for feature, value in ENV_LABSTER_FEATURES.items():
    FEATURES[feature] = value

INSTALLED_APPS += (
    'rest_framework.authtoken',
    'labster',
)

LABSTER_WIKI_LINK = ENV_TOKENS.get('LABSTER_WIKI_LINK', 'http://theory.labster.com/')
