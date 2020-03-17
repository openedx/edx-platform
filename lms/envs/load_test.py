"""
Settings for load testing.
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=wildcard-import, unused-wildcard-import


from six.moves import filter

from .production import *

# Disable CSRF for load testing
EXCLUDE_CSRF = lambda elem: elem not in [
    'django.template.context_processors.csrf',
    'django.middleware.csrf.CsrfViewMiddleware'
]
DEFAULT_TEMPLATE_ENGINE['OPTIONS']['context_processors'] = list(filter(
    EXCLUDE_CSRF, DEFAULT_TEMPLATE_ENGINE['OPTIONS']['context_processors']
))
MIDDLEWARE = list(filter(EXCLUDE_CSRF, MIDDLEWARE))
