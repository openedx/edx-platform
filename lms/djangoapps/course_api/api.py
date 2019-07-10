"""
Course API
"""

from __future__ import absolute_import

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from rest_framework.exceptions import PermissionDenied
import search
import six

from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.courseware.courses import (
    get_course_overview_with_access,
    get_courses,
    get_permission_for_course_about
)
from openedx.core.lib.api.view_utils import LazySequence

from .permissions import can_view_courses_for_username


def get_effective_user(requesting_user, target_username):
    """
    Get the user we want to view information on behalf of.
    """
    if target_username == requesting_user.username:
        return requesting_user
    elif target_username == '':
        return AnonymousUser()
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
        `CourseOverview` object representing the requested course
    """
    user = get_effective_user(request.user, username)
    return get_course_overview_with_access(
        user,
        get_permission_for_course_about(),
        course_key,
    )


def _filter_courses_by_role(course_queryset, user, access_type):
    """
    Return a course queryset filtered by the access type for which the user has access.
    """
    return LazySequence(
        (
            course for course in course_queryset
            if has_access(user, access_type, course.id)
        ),
        est_len=len(course_queryset)
    )


def list_courses(request, username, org=None, roles=None, filter_=None, search_term=None):
    """
    Yield all available courses.

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

    Keyword Arguments:
        org (string):
            If specified, visible `CourseOverview` objects are filtered
            such that only those belonging to the organization with the provided
            org code (e.g., "HarvardX") are returned. Case-insensitive.
        roles (list of strings):
            If specified, visible `CourseOverview` objects are filtered
            such that only those for which the user has the specified role(s)
            are returned. Multiple role parameters can be specified.
        filter_ (dict):
            If specified, visible `CourseOverview` objects are filtered
            by the given key-value pairs.
        search_term (string):
            Search term to filter courses (used by ElasticSearch).

    Return value:
        Yield `CourseOverview` objects representing the collection of courses.
    """
    user = get_effective_user(request.user, username)
    course_qs = get_courses(user, org=org, filter_=filter_)

    # Global staff have access to all courses. Filter course roles for non-global staff only.
    if not user.is_staff:
        if roles:
            for role in roles:
                # Filter the courses again to return only the courses for which the user has the specified roles.
                course_qs = _filter_courses_by_role(course_qs, user, role)

    if not settings.FEATURES['ENABLE_COURSEWARE_SEARCH'] or not search_term:
        return course_qs

    # Return all the results, 10K is the maximum allowed value for ElasticSearch.
    # We should use 0 after upgrading to 1.1+:
    #   - https://github.com/elastic/elasticsearch/commit/8b0a863d427b4ebcbcfb1dcd69c996c52e7ae05e
    results_size_infinity = 10000

    search_courses = search.api.course_discovery_search(
        search_term,
        size=results_size_infinity,
    )

    search_courses_ids = {course['data']['id'] for course in search_courses['results']}

    return LazySequence(
        (
            course for course in course_qs
            if six.text_type(course.id) in search_courses_ids
        ),
        est_len=len(course_qs)
    )
