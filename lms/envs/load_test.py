# Settings for load testing

from .aws import *

# Disable CSRF for load testing
exclude_csrf = lambda elem: not elem in \
               ['django.core.context_processors.csrf',
                'django.middleware.csrf.CsrfViewMiddleware']
TEMPLATE_CONTEXT_PROCESSORS = filter(exclude_csrf, TEMPLATE_CONTEXT_PROCESSORS)
MIDDLEWARE_CLASSES = filter(exclude_csrf, MIDDLEWARE_CLASSES)
