from .aws import *

INSTALLED_APPS += ('appsembler_cms', 'appsembler_lms',)

APPSEMBLER_SECRET_KEY = AUTH_TOKENS.get("APPSEMBLER_SECRET_KEY")
OAUTH_ENFORCE_SECURE = True
