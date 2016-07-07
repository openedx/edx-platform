# devstack_appsembler.py

from .devstack import *
from .appsembler import *

INSTALLED_APPS += (
    'appsembler.enrollment_api',
    'appsembler.ps_user_api',
)
