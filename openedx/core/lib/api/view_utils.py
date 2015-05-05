"""
Utilities related to API views
"""
from django.http import Http404

from rest_framework.exceptions import APIException
from rest_framework.response import Response


class DeveloperErrorViewMixin(object):
    """
    A view mixin to handle common error cases other than validation failure
    (auth failure, method not allowed, etc.) by generating an error response
    conforming to our API conventions with a developer message.
    """
    def make_error_response(self, status_code, developer_message):
        """
        Build an error response with the given status code and developer_message
        """
        return Response({"developer_message": developer_message}, status=status_code)

    def handle_exception(self, exc):
        if isinstance(exc, APIException):
            return self.make_error_response(exc.status_code, exc.detail)
        elif isinstance(exc, Http404):
            return self.make_error_response(404, "Not found.")
        else:
            raise
