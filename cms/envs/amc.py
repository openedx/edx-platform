from .aws import *

INSTALLED_APPS += ('appsembler_cms', 'appsembler_lms',)

APPSEMBLER_SECRET_KEY = AUTH_TOKENS.get("secret_key")
OAUTH_ENFORCE_SECURE = True
