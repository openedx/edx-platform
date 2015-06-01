"""
Utilities related to API views
"""
import functools
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.http import Http404

from rest_framework import status, response
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from lms.djangoapps.courseware.courses import get_course_with_access
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore

from openedx.core.lib.api.authentication import (
    SessionAuthenticationAllowInactiveUser,
    OAuth2AuthenticationAllowInactiveUser,
)
from openedx.core.lib.api.permissions import IsUserInUrl, IsAuthenticatedOrDebug
from util.milestones_helpers import any_unfulfilled_milestones


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
            # Extract both Django form and DRF serializer non-field errors
            non_field_error_list = (
                message_dict.pop(NON_FIELD_ERRORS, []) +
                message_dict.pop("non_field_errors", [])
            )
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


def view_course_access(depth=0, access_action='load', check_for_milestones=False):
    """
    Method decorator for an API endpoint that verifies the user has access to the course.
    """
    def _decorator(func):
        """Outer method decorator."""
        @functools.wraps(func)
        def _wrapper(self, request, *args, **kwargs):
            """
            Expects kwargs to contain 'course_id'.
            Passes the course descriptor to the given decorated function.
            Raises 404 if access to course is disallowed.
            """
            course_id = CourseKey.from_string(kwargs.pop('course_id'))
            with modulestore().bulk_operations(course_id):
                try:
                    course = get_course_with_access(
                        request.user,
                        access_action,
                        course_id,
                        depth=depth
                    )
                except Http404:
                    # any_unfulfilled_milestones called a second time since has_access returns a bool
                    if check_for_milestones and any_unfulfilled_milestones(course_id, request.user.id):
                        message = {
                            "developer_message": "Cannot access content with unfulfilled "
                                                 "pre-requisites or unpassed entrance exam."
                        }
                        return response.Response(data=message, status=status.HTTP_204_NO_CONTENT)
                    else:
                        raise
                return func(self, request, course=course, *args, **kwargs)
        return _wrapper
    return _decorator


def view_auth_classes(is_user=False):
    """
    Function and class decorator that abstracts the authentication and permission checks for api views.
    """
    def _decorator(func_or_class):
        """
        Requires either OAuth2 or Session-based authentication.
        If is_user is True, also requires username in URL matches the request user.
        """
        func_or_class.authentication_classes = (
            OAuth2AuthenticationAllowInactiveUser,
            SessionAuthenticationAllowInactiveUser
        )
        func_or_class.permission_classes = (IsAuthenticatedOrDebug,)
        if is_user:
            func_or_class.permission_classes += (IsUserInUrl,)
        return func_or_class
    return _decorator
