"""
Common utility methods and decorators for Mobile APIs.
"""

import functools

from django.http import Http404

from rest_framework import permissions, status, response

from opaque_keys.edx.keys import CourseKey

from courseware.courses import get_course_with_access
from openedx.core.lib.api.permissions import IsUserInUrl
from openedx.core.lib.api.authentication import (
    SessionAuthenticationAllowInactiveUser,
    OAuth2AuthenticationAllowInactiveUser,
)
from util.milestones_helpers import any_unfulfilled_milestones
from xmodule.modulestore.django import modulestore


def mobile_course_access(depth=0, verify_enrolled=True):
    """
    Method decorator for a mobile API endpoint that verifies the user has access to the course in a mobile context.
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
                        'load_mobile' if verify_enrolled else 'load_mobile_no_enrollment_check',
                        course_id,
                        depth=depth
                    )
                except Http404:
                    # any_unfulfilled_milestones called a second time since get_course_with_access returns a bool
                    if any_unfulfilled_milestones(course_id, request.user.id):
                        message = {
                            "developer_message": "Cannot access content with unfulfilled pre-requisites or unpassed entrance exam."  # pylint: disable=line-too-long
                        }
                        return response.Response(
                            data=message,
                            status=status.HTTP_204_NO_CONTENT
                        )
                    else:
                        raise
                return func(self, request, course=course, *args, **kwargs)
        return _wrapper
    return _decorator


def mobile_view(is_user=False):
    """
    Function and class decorator that abstracts the authentication and permission checks for mobile api views.
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
        func_or_class.permission_classes = (permissions.IsAuthenticated,)
        if is_user:
            func_or_class.permission_classes += (IsUserInUrl,)
        return func_or_class
    return _decorator
