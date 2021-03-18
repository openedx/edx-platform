"""
Course API
"""
import logging

import search
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User  # lint-amnesty, pylint: disable=imported-auth-user
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.urls import reverse
from edx_django_utils.monitoring import function_trace
from edx_when.api import get_dates_for_course
from opaque_keys.edx.django.models import CourseKeyField
from rest_framework.exceptions import PermissionDenied

from common.djangoapps.student.models import CourseAccessRole, CourseEnrollment
from common.djangoapps.student.roles import GlobalStaff, REGISTERED_ACCESS_ROLES
from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.course_api.serializers import CourseMemberSerializer
from lms.djangoapps.courseware.courses import (
    get_course_overview_with_access,
    get_courses,
    get_permission_for_course_about
)
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.lib.api.view_utils import LazySequence
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

from .permissions import can_view_courses_for_username

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


UNKNOWN_BLOCK_DISPLAY_NAME = 'UNKNOWN'


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
    overview = get_course_overview_with_access(
        user,
        get_permission_for_course_about(),
        course_key,
    )
    overview.effective_user = user
    return overview


def _filter_by_search(course_queryset, search_term):
    """
    Filters a course queryset by the specified search term.
    """
    if not settings.FEATURES['ENABLE_COURSEWARE_SEARCH'] or not search_term:
        return course_queryset

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
            course for course in course_queryset
            if str(course.id) in search_courses_ids
        ),
        est_len=len(course_queryset)
    )


def list_courses(request, username, org=None, filter_=None, search_term=None):
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
    course_qs = _filter_by_search(course_qs, search_term)
    return course_qs


@function_trace('list_course_keys')
def list_course_keys(request, username, role):
    """
    Yield all available CourseKeys for the user having the given role.

    The courses returned include those for which the user identified by
    `username` has the given role.  Additionally, the logged in user
    should have permission to view courses available to that user.

    Note: This function does not use branding to determine courses.

    Arguments:
        request (HTTPRequest):
            Used to identify the logged-in user and to instantiate the course
            module to retrieve the course about description
        username (string):
            The name of the user the logged-in user would like to be
            identified as

    Keyword Arguments:
        role (string):
            Course keys are filtered such that only those for which the
            user has the specified role are returned.

    Return value:
        Yield `CourseKey` objects representing the collection of courses.

    """
    user = get_effective_user(request.user, username)

    all_course_keys = CourseOverview.get_all_course_keys()

    # Global staff have access to all courses. Filter courses for non-global staff.
    if GlobalStaff().has_user(user):
        return all_course_keys

    if role == 'staff':
        # This short-circuit implementation bypasses has_access() which we think is too slow for some users when
        # evaluating staff-level course access for Insights.  Various tickets have context on this issue: CR-2487,
        # TNL-7448, DESUPPORT-416, and probably more.
        #
        # This is a simplified implementation that does not consider org-level access grants (e.g. when course_id is
        # empty).
        filtered_course_keys = (
            CourseAccessRole.objects.filter(
                user=user,
                # Having the instructor role implies staff access.
                role__in=['staff', 'instructor'],
            )
            # We need to check against CourseOverview so that we don't return any Libraries.
            .extra(tables=['course_overviews_courseoverview'], where=['course_id = course_overviews_courseoverview.id'])
            # For good measure, make sure we don't return empty course IDs.
            .exclude(course_id=CourseKeyField.Empty)
            .order_by('course_id')
            .values_list('course_id', flat=True)
            .distinct()
        )
    else:
        # This is the original implementation which still covers the case where role = "instructor":
        filtered_course_keys = LazySequence(
            (
                course_key for course_key in all_course_keys
                if has_access(user, role, course_key)
            ),
            est_len=len(all_course_keys)
        )
    return filtered_course_keys


def get_due_dates(request, course_key, user):
    """
    Get due date information for a user for blocks in a course.

    Arguments:
        request: the request object
        course_key (CourseKey): the CourseKey for the course
        user: the user object for which we want due date information

    Returns:
        due_dates (list): a list of dictionaries containing due date information
            keys:
                name: the display name of the block
                url: the deep link to the block
                date: the due date for the block
    """
    dates = get_dates_for_course(
        course_key,
        user,
    )

    store = modulestore()

    due_dates = []
    for (block_key, date_type), date in dates.items():
        if date_type == 'due':
            try:
                block_display_name = store.get_item(block_key).display_name
            except ItemNotFoundError:
                logger.exception(f'Failed to get block for due date item with key: {block_key}')
                block_display_name = UNKNOWN_BLOCK_DISPLAY_NAME

            # get url to the block in the course
            block_url = reverse('jump_to', args=[course_key, block_key])
            block_url = request.build_absolute_uri(block_url)

            due_dates.append({
                'name': block_display_name,
                'url': block_url,
                'date': date,
            })
    return due_dates


def get_course_run_url(request, course_id):
    """
    Get the URL to a course run.

    Arguments:
        request: the request object
        course_id (string): the course id of the course

    Returns:
        (string): the URL to the course run associated with course_id
    """
    course_run_url = reverse('openedx.course_experience.course_home', args=[course_id])
    return request.build_absolute_uri(course_run_url)


def get_course_members(course_key, include_students=True, access_roles=None, page=1, limit=20):
    """
    Returns a dict containing User information that filters all users related to a course.
    For example - Students, Teachers, Staffs etc.

    User information includes -
        - User info - id, email, username
        - Profile info - name, picture etc
        - CourseEnrollment - mode, only the course enrollments associated with the given course
        - CourseAccessRole - role, only the course access roles associated with the given course

    Examples:
        - Get all members:
            get_course_members(course_key)
        - Get only students excluding staffs:
            get_course_members(course_key, include_students=True, access_roles=[])
        - Get only staffs excluding students:
            get_course_members(course_key, include_students=False, access_roles=None)
        - Get only instructors:
            get_course_members(course_key, include_students=False, access_roles=['instructor'])
        - Get instructors & students:
            get_course_members(course_key, include_students=True, access_roles=['instructor'])
        - Paginating
            get_course_members(course_key, page=2)
        - Paginating with custom limit
            get_course_members(course_key, limit=50)

    Arguments:
        course_key (CourseKey): the CourseKey for the course
        include_students: wether or not to include students,
        access_roles:
            accepts an array of string course access roles.
            If None provided, it includes all roles.
        page (int): the page number for pagination
        limit (int): how many results to include per page

    Returns:
        dict: A dictionary with paginated result with following format -
            {
                'count': total number of user instances matching specified filter,
                'num_pages': total number of pages,
                'current_page': current page number,
                'result': [
                    {
                        'id': user id,
                        'email': user's email,
                        'username': user's username,
                        'profile': {
                            'name': user's name,
                            'profile_image': user's profile image,
                            .... other profile information
                        },
                        'enrollments': [
                            {
                                'mode': enrollment mode
                            }
                        ],
                        'course_access_roles': [
                            {
                                'role': user's role in course
                            }
                        ]
                    }
                ]
            }
    """
    queryset = User.objects.filter(is_active=True).order_by('id')

    # if access_roles not given, assign all registered access roles
    if access_roles is None:
        access_roles = list(REGISTERED_ACCESS_ROLES.keys())

    # conditions for filtering based on CourseAccessRole
    access_role_qs = Q(
        courseaccessrole__course_id=course_key,
        courseaccessrole__role__in=access_roles
    )

    # conditions for filtering based on CourseEnrollment
    students_qs = Q(
        courseenrollment__course_id=course_key,
        courseenrollment__is_active=True
    )

    if include_students:
        queryset = queryset.filter(access_role_qs | students_qs)
    else:
        queryset = queryset.filter(access_role_qs)

    # prevent duplicates
    queryset = queryset.distinct()

    # prefetch UserProfile
    queryset = queryset.prefetch_related('profile')

    # prefetch CourseAccessRole items related to the course and given roles
    queryset = queryset.prefetch_related(Prefetch(
        'courseaccessrole_set',
        CourseAccessRole.objects.filter(
            course_id=course_key, role__in=access_roles)
    ))

    # prefetch CourseEnrollment items related to the course
    queryset = queryset.prefetch_related(Prefetch(
        'courseenrollment_set',
        CourseEnrollment.objects.filter(course_id=course_key)
    ))

    paginator = Paginator(queryset, limit)

    serialized_data = CourseMemberSerializer(paginator.page(page), many=True).data

    return {
        'count': paginator.count,
        'num_pages': paginator.num_pages,
        'current_page': page,
        'result': serialized_data,
    }
