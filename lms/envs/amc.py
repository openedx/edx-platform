from .aws import *

APPSEMBLER_SECRET_KEY = AUTH_TOKENS.get("APPSEMBLER_SECRET_KEY")
# the following ip should work for all dev setups....
APPSEMBLER_AMC_API_BASE = AUTH_TOKENS.get('APPSEMBLER_AMC_API_BASE')
APPSEMBLER_FIRST_LOGIN_API = '/logged_into_edx'

# needed to show only users and appsembler courses
#FEATURES["ENABLE_COURSE_DISCOVERY"] = False
FEATURES["SHOW_ONLY_APPSEMBLER_AND_OWNED_COURSES"] = True

EMAIL_BACKEND = 'django_mailgun.MailgunBackend'
MAILGUN_ACCESS_KEY = AUTH_TOKENS.get("MAILGUN_ACCESS_KEY")
MAILGUN_SERVER_NAME = AUTH_TOKENS.get("MAILGUN_SERVER_NAME")

INSTALLED_APPS += ('appsembler_lms',)
