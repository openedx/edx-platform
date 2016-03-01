from .aws import *

APPSEMBLER_SECRET_KEY = AUTH_TOKENS.get("secret_key")
# the following ip should work for all dev setups....
APPSEMBLER_AMC_API_BASE = ENV_TOKENS.get('http://10.0.2.2:8080/api')
APPSEMBLER_FIRST_LOGIN_API = '/logged_into_edx'

# needed to show only users and appsembler courses
#FEATURES["ENABLE_COURSE_DISCOVERY"] = False
FEATURES["SHOW_ONLY_APPSEMBLER_AND_OWNED_COURSES"] = True
OAUTH_ENFORCE_SECURE = True

INSTALLED_APPS += ('appsembler_lms',)
