# devstack_appsembler.py

from .devstack import *
from .appsembler import *

INSTALLED_APPS += (
    'appsembler.enrollment_api',
    'appsembler.ps_user_api',
)

CUSTOM_LOGOUT_REDIRECT_URL = ENV_TOKENS.get('CUSTOM_LOGOUT_REDIRECT_URL', '/')