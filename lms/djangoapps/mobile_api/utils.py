"""
Common utility methods and decorators for Mobile APIs.
"""


import functools
from contextlib import contextmanager
from django.http import Http404
from django.conf import settings

from opaque_keys.edx.keys import CourseKey
from courseware.courses import get_course_with_access
from rest_framework import permissions
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication


# TODO This contextmanager should be moved to a common utility library.
@contextmanager
def dict_value(dictionary, key, value):
    """
    A context manager that assigns 'value' to the 'key' in the 'dictionary' when entering the context,
    and then resets the key upon exiting the context.
    """

    # cache previous values
    has_previous_value = key in dictionary
    previous_value = dictionary[key] if has_previous_value else None

    try:
        # temporarily set to new value
        dictionary[key] = value
        yield
    finally:
        # reset to previous values
        if has_previous_value:
            dictionary[key] = previous_value
        else:
            dictionary.pop(key, None)


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


def mobile_course_listing_access(course, user):
    """
    Determines whether a user has access to a course' listing in a mobile context.
        Checks the mobile_available flag.
        Checks roles including Beta Tester and staff roles.
    Note:
        Does not check if the user is actually enrolled in the course.
        Does not check the start_date.
    """
    # The course doesn't always really exist -- we can have bad data in the enrollments
    # pointing to non-existent (or removed) courses, in which case `course` is None.
    if not course:
        return False
    try:
        with dict_value(settings.FEATURES, 'DISABLE_START_DATES', True):
            return get_course_with_access(user, 'load_mobile_no_enrollment_check', course.id) is not None
    except Http404:
        return False


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
