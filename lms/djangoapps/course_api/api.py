"""
Course API
"""

from django.contrib.auth.models import User
from django.http import Http404
from rest_framework.exceptions import NotFound, PermissionDenied

from lms.djangoapps.courseware.courses import get_courses, get_course_with_access

from .permissions import can_view_courses_for_username
from .serializers import CourseSerializer


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
        CourseSerializer object representing the requested course
    """
    user = get_effective_user(request.user, username)
    try:
        course = get_course_with_access(user, 'see_exists', course_key)
    except Http404:
        raise NotFound()
    return CourseSerializer(course, context={'request': request}).data


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
        A CourseSerializer object representing the collection of courses.
    """
    user = get_effective_user(request.user, username)
    courses = get_courses(user)
    return CourseSerializer(courses, context={'request': request}, many=True).data
