from .devstack import *

INSTALLED_APPS += ('appsembler_cms', 'appsembler_lms',)

APPSEMBLER_SECRET_KEY = "secret_key"
OAUTH_ENFORCE_SECURE = False
