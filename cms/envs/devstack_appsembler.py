# devstack_appsembler.py

from .devstack import *
from .appsembler import *

CUSTOM_LOGOUT_REDIRECT_URL = ENV_TOKENS.get('CUSTOM_LOGOUT_REDIRECT_URL', '/')