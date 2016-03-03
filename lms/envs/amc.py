from .aws import *
from .appsembler import *

APPSEMBLER_SECRET_KEY = APPSEMBLER_FEATURES.get("APPSEMBLER_SECRET_KEY")
# the following ip should work for all dev setups....
APPSEMBLER_AMC_API_BASE = APPSEMBLER_FEATURES.get('APPSEMBLER_AMC_API_BASE')
APPSEMBLER_FIRST_LOGIN_API = '/logged_into_edx'

# needed to show only users and appsembler courses
#FEATURES["ENABLE_COURSE_DISCOVERY"] = False
FEATURES["SHOW_ONLY_APPSEMBLER_AND_OWNED_COURSES"] = True

INSTALLED_APPS += ('appsembler_lms',)
