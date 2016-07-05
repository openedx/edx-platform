# devstack_appsembler.py

from .devstack import *
from .appsembler import *

INSTALLED_APPS += (
    'appsembler.intercom_integration',
    'appsembler.enrollment_api'
    'appsembler.ps_user_api',
)
DEFAULT_TEMPLATE_ENGINE['OPTIONS']['context_processors'] += ('appsembler.intercom_integration.context_processors.intercom',)
