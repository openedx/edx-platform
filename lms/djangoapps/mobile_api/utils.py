"""
Common utility methods and decorators for Mobile APIs.
"""


import functools

from opaque_keys.edx.keys import CourseKey
from courseware.courses import get_course_with_access
from rest_framework import permissions
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication


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
            course = get_course_with_access(
                request.user,
                'load_mobile' if verify_enrolled else 'load_mobile_no_enrollment_check',
                course_id,
                depth=depth
            )
            return func(self, request, course=course, *args, **kwargs)
        return _wrapper
    return _decorator


def mobile_view(is_user=False):
    """
    Function and class decorator that abstracts the authentication and permission checks for mobile api views.
    """
    class IsUser(permissions.BasePermission):
        """
        Permission that checks to see if the request user matches the user in the URL.
        """
        def has_permission(self, request, view):
            return request.user.username == request.parser_context.get('kwargs', {}).get('username', None)

    def _decorator(func_or_class):
        """
        Requires either OAuth2 or Session-based authentication.
        If is_user is True, also requires username in URL matches the request user.
        """
        func_or_class.authentication_classes = (OAuth2Authentication, SessionAuthentication)
        func_or_class.permission_classes = (permissions.IsAuthenticated,)
        if is_user:
            func_or_class.permission_classes += (IsUser,)
        return func_or_class
    return _decorator
