"""
Middleware to add correct x-frame-options headers.

The headers get set to the platform default which we assume is `DENY`.
However, there's a number of paths that are set to `SAMEORIGIN` which
we identify via regexes stored in a django setting in the application calling this.
"""

import re

from django.conf import settings
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.middleware.clickjacking import XFrameOptionsMiddleware

PERMISSIBLE_VALUES = ['DENY', 'SAMEORIGIN', 'ALLOW']


class InvalidHeaderValueError(ValueError):
    """ A custom error that is thrown when we try to set an invalid value for a header """
    pass


def _validate_header_value(value):
    if value not in PERMISSIBLE_VALUES:
        raise InvalidHeaderValueError(
            f'Invalid value "{value}" for header "X-Frame-Options"'
        )


class EdxXFrameOptionsMiddleware(XFrameOptionsMiddleware):
    """
    A class extending the django XFrameOptionsMiddleware with the ability to override
    the header for URLs specified in a `X_FRAME_OPTIONS_OVERRIDES` django setting.
    You can set this via `X_FRAME_OPTIONS_OVERRIDES = [[regex, value]]` in your django application
    where you specify a list of pairs of regex and value, where regex matches urls and value is
    one of `DENY`, `SAMEORIGIN`, `ALLOW`. The latter is not advisable unless you have a content security
    policy in place.
    """
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """
        Process the response and set the x-frame-options header to the value specified
        """
        response = super().process_response(request, response)
        headers = response.headers
        request_path = request.path
        frame_options = getattr(settings, 'X_FRAME_OPTIONS', 'DENY')
        _validate_header_value(frame_options)

        headers['X-Frame-Options'] = frame_options
        overrides = getattr(settings, 'X_FRAME_OPTIONS_OVERRIDES', [])
        for override in overrides:
            print('override', override)
            regex, value = override
            _validate_header_value(value)
            if re.search(regex, request_path):
                headers['X-Frame-Options'] = value
        response.headers = headers
        return response
