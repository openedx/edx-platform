"""
Utilities related to API views
"""
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
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

    def make_validation_error_response(self, validation_error):
        """
        Build a 400 error response from the given ValidationError
        """
        if hasattr(validation_error, "message_dict"):
            response_obj = {}
            message_dict = dict(validation_error.message_dict)
            non_field_error_list = message_dict.pop(NON_FIELD_ERRORS, None)
            if non_field_error_list:
                response_obj["developer_message"] = non_field_error_list[0]
            if message_dict:
                response_obj["field_errors"] = {
                    field: {"developer_message": message_dict[field][0]}
                    for field in message_dict
                }
            return Response(response_obj, status=400)
        else:
            return self.make_error_response(400, validation_error.messages[0])

    def handle_exception(self, exc):
        if isinstance(exc, APIException):
            return self.make_error_response(exc.status_code, exc.detail)
        elif isinstance(exc, Http404):
            return self.make_error_response(404, "Not found.")
        elif isinstance(exc, ValidationError):
            return self.make_validation_error_response(exc)
        else:
            raise
