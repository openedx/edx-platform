# aws_appsembler.py

from .aws import *
from .appsembler import *


INSTALLED_APPS += (
    'appsembler_common.intercom_integration',
    'appsembler.enrollment_api',
    'appsembler.ps_user_api',
)

DEFAULT_TEMPLATE_ENGINE['OPTIONS']['context_processors'] += (
    'appsembler_common.intercom_integration.context_processors.intercom',
)

SEARCH_SKIP_ENROLLMENT_START_DATE_FILTERING = True

#enable course visibility feature flags
COURSE_CATALOG_VISIBILITY_PERMISSION = 'see_in_catalog'
COURSE_ABOUT_VISIBILITY_PERMISSION = 'see_about_page'

CUSTOM_LOGOUT_REDIRECT_URL = ENV_TOKENS.get('CUSTOM_LOGOUT_REDIRECT_URL', '/')