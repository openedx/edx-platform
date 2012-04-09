"""
These are debug machines used for content creators, so they're kind of a cross
between dev machines and AWS machines.
"""
from aws import *

DEBUG = True
TEMPLATE_DEBUG = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
