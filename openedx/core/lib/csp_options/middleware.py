"""
Middleware to override CSP headers.
"""

import re

from django.conf import settings
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.middleware.clickjacking import XFrameOptionsMiddleware

PERMISSIBLE_DIRECTIVES = ["'self'", "'none'"]


class InvalidHeaderValueError(ValueError):
    """ A custom error that is thrown when we try to set an invalid value for a header """


def _validate_header_value(value):
    """
    Check for permissible directives when value is surrounded in single quotes.
    """
    if value not in PERMISSIBLE_DIRECTIVES:
        raise InvalidHeaderValueError(
            f'Invalid value "{value}" for header "CSP frame ancestors"'
        )


class EdxCSPOptionsMiddleware(XFrameOptionsMiddleware):
    """
    CSP Middleware
    """
