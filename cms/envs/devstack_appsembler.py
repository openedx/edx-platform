from .devstack import *

INSTALLED_APPS += ('appsembler_lms',)
FEATURES['APPSEMBLER_SECRET_KEY'] = "secret_key"
OAUTH_ENFORCE_SECURE = False
