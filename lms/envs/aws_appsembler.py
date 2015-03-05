# aws_appsembler.py

from .aws import *
from .appsembler import *

INSTALLED_APPS += ('appsembler',)
TEMPLATE_CONTEXT_PROCESSORS += ('appsembler.context_processors.intercom',)
