"""
Course API
"""

from django.contrib.auth.models import User
from rest_framework.exceptions import PermissionDenied

from lms.djangoapps.courseware.courses import (
    get_courses,
    get_course_overview_with_access,
    get_permission_for_course_about,
)

from .permissions import can_view_courses_for_username


def get_effective_user(requesting_user, target_username):
    """
    Get the user we want to view information on behalf of.
    """
    if target_username == requesting_user.username:
        return requesting_user
    elif can_view_courses_for_username(requesting_user, target_username):
        return User.objects.get(username=target_username)
    else:
        raise PermissionDenied()


def course_detail(request, username, course_key):
    """
    Return a single course identified by `course_key`.

    The course must be visible to the user identified by `username` and the
    logged-in user should have permission to view courses available to that
    user.

    Arguments:
        request (HTTPRequest):
            Used to identify the logged-in user and to instantiate the course
            module to retrieve the course about description
        username (string):
            The name of the user `requesting_user would like to be identified as.
        course_key (CourseKey): Identifies the course of interest

    Return value:
        `CourseDescriptor` object representing the requested course
    """
    user = get_effective_user(request.user, username)
    return get_course_overview_with_access(
        user,
        get_permission_for_course_about(),
        course_key,
    )


def list_courses(request, username):
    """
    Return a list of available courses.

    The courses returned are all be visible to the user identified by
    `username` and the logged in user should have permission to view courses
    available to that user.

    Arguments:
        request (HTTPRequest):
            Used to identify the logged-in user and to instantiate the course
            module to retrieve the course about description
        username (string):
            The name of the user the logged-in user would like to be
            identified as


    Return value:
        List of `CourseDescriptor` objects representing the collection of courses.
    """
    user = get_effective_user(request.user, username)
    return get_courses(user)
