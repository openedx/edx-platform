"""
Settings for load testing.
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=wildcard-import, unused-wildcard-import

from .aws import *

# TODO: Remove Django 1.11 upgrade shim
# SHIM: Remove birdcage references post-1.11 upgrade as it is only in place to help during that deployment

# Disable CSRF for load testing
EXCLUDE_CSRF = lambda elem: elem not in [
    'django.template.context_processors.csrf',
    'django.middleware.csrf.CsrfViewMiddleware',
    'birdcage.v1_11.csrf.CsrfViewMiddleware'
]
DEFAULT_TEMPLATE_ENGINE['OPTIONS']['context_processors'] = filter(
    EXCLUDE_CSRF, DEFAULT_TEMPLATE_ENGINE['OPTIONS']['context_processors']
)
MIDDLEWARE_CLASSES = filter(EXCLUDE_CSRF, MIDDLEWARE_CLASSES)
