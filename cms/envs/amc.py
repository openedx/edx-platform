from .aws import *

APPSEMBLER_AMC_API_BASE = AUTH_TOKENS.get('APPSEMBLER_AMC_API_BASE')
APPSEMBLER_FIRST_LOGIN_API = '/logged_into_edx'

APPSEMBLER_SECRET_KEY = AUTH_TOKENS.get("APPSEMBLER_SECRET_KEY")

INSTALLED_APPS += (
    'openedx.core.djangoapps.appsembler.sites',
)

DEFAULT_TEMPLATE_ENGINE['OPTIONS']['context_processors'] += ('openedx.core.djangoapps.appsembler.intercom_integration.context_processors.intercom',)

MANDRILL_API_KEY = AUTH_TOKENS.get("MANDRILL_API_KEY")

if MANDRILL_API_KEY:
    EMAIL_BACKEND = ENV_TOKENS.get('EMAIL_BACKEND', 'anymail.backends.mandrill.MandrillBackend')
    ANYMAIL = {
        "MANDRILL_API_KEY": MANDRILL_API_KEY,
    }
    INSTALLED_APPS += ("anymail",)

INTERCOM_APP_ID = AUTH_TOKENS.get("INTERCOM_APP_ID")
INTERCOM_APP_SECRET = AUTH_TOKENS.get("INTERCOM_APP_SECRET")

FEATURES['ENABLE_COURSEWARE_INDEX'] = True
FEATURES['ENABLE_LIBRARY_INDEX'] = True

SEARCH_ENGINE = "search.elastic.ElasticSearchEngine"
ELASTIC_FIELD_MAPPINGS = {
    "start_date": {
        "type": "date"
    }
}

