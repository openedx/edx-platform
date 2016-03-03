from .aws import *

INSTALLED_APPS += ('appsembler_cms', 'appsembler_lms',)

APPSEMBLER_SECRET_KEY = APPSEMBLER_FEATURES.get("APPSEMBLER_SECRET_KEY")
