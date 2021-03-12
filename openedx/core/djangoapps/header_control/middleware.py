"""
Middleware used for adjusting headers in a response before it is sent to the end user.
"""

from django.utils.deprecation import MiddlewareMixin
import six


class HeaderControlMiddleware(MiddlewareMixin):
    """
    Middleware that can modify/remove headers in a response.

    This can be used, for example, to remove headers i.e. drop any Vary headers to improve cache performance.
    """

    def process_response(self, _request, response):
        """
        Processes the given response, potentially remove or modifying headers.
        """

        for header in getattr(response, 'remove_headers', []):
            del response[header]

        for header, value in six.iteritems(getattr(response, 'force_headers', {})):
            response[header] = value

        return response
