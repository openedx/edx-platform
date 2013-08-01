"""
Settings for load testing.
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=W0401, W0614

from .aws import *

# Disable CSRF for load testing
exclude_csrf = lambda elem: not elem in \
               ['django.core.context_processors.csrf',
                'django.middleware.csrf.CsrfViewMiddleware']
TEMPLATE_CONTEXT_PROCESSORS = filter(exclude_csrf, TEMPLATE_CONTEXT_PROCESSORS)
MIDDLEWARE_CLASSES = filter(exclude_csrf, MIDDLEWARE_CLASSES)
