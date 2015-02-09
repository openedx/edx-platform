from .aws import *

INSTALLED_APPS += ('appsembler',)

TEMPLATE_CONTEXT_PROCESSORS += ('appsembler.context_processors.intercom',)