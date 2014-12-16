"""
Settings for load testing.
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=wildcard-import, unused-wildcard-import

from .aws import *

# Disable CSRF for load testing
EXCLUDE_CSRF = lambda elem: elem not in [
    'django.core.context_processors.csrf',
    'django.middleware.csrf.CsrfViewMiddleware'
]
TEMPLATE_CONTEXT_PROCESSORS = filter(EXCLUDE_CSRF, TEMPLATE_CONTEXT_PROCESSORS)
MIDDLEWARE_CLASSES = filter(EXCLUDE_CSRF, MIDDLEWARE_CLASSES)
