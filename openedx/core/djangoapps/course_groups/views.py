"""
Views related to course groups functionality.
"""

from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from util.json_request import expect_json, JsonResponse
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext

import logging
import re

from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from courseware.courses import get_course_with_access
from edxmako.shortcuts import render_to_response

from . import cohorts
from lms.djangoapps.django_comment_client.utils import get_discussion_category_map, get_discussion_categories_ids
from lms.djangoapps.django_comment_client.constants import TYPE_ENTRY
from .models import CourseUserGroup, CourseUserGroupPartitionGroup, CohortMembership

log = logging.getLogger(__name__)


def json_http_response(data):
    """
    Return an HttpResponse with the data json-serialized and the right content
    type header.
    """
    return JsonResponse(data)


def split_by_comma_and_whitespace(cstr):
    """
    Split a string both by commas and whitespace.  Returns a list.
    """
    return re.split(r'[\s,]+', cstr)


def link_cohort_to_partition_group(cohort, partition_id, group_id):
    """
    Create cohort to partition_id/group_id link.
    """
    CourseUserGroupPartitionGroup(
        course_user_group=cohort,
        partition_id=partition_id,
        group_id=group_id,
    ).save()


def unlink_cohort_partition_group(cohort):
    """
    Remove any existing cohort to partition_id/group_id link.
    """
    CourseUserGroupPartitionGroup.objects.filter(course_user_group=cohort).delete()


# pylint: disable=invalid-name
def _get_course_cohort_settings_representation(course, course_cohort_settings):
    """
    Returns a JSON representation of a course cohort settings.
    """
    cohorted_course_wide_discussions, cohorted_inline_discussions = get_cohorted_discussions(
        course, course_cohort_settings
    )

    return {
        'id': course_cohort_settings.id,
        'is_cohorted': course_cohort_settings.is_cohorted,
        'cohorted_inline_discussions': cohorted_inline_discussions,
        'cohorted_course_wide_discussions': cohorted_course_wide_discussions,
        'always_cohort_inline_discussions': course_cohort_settings.always_cohort_inline_discussions,
    }


def _get_cohort_representation(cohort, course):
    """
    Returns a JSON representation of a cohort.
    """
    group_id, partition_id = cohorts.get_group_info_for_cohort(cohort)
    assignment_type = cohorts.get_assignment_type(cohort)
    return {
        'name': cohort.name,
        'id': cohort.id,
        'user_count': cohort.users.count(),
        'assignment_type': assignment_type,
        'user_partition_id': partition_id,
        'group_id': group_id,
    }


def get_cohorted_discussions(course, course_settings):
    """
    Returns the course-wide and inline cohorted discussion ids separately.
    """
    cohorted_course_wide_discussions = []
    cohorted_inline_discussions = []

    course_wide_discussions = [topic['id'] for __, topic in course.discussion_topics.items()]
    all_discussions = get_discussion_categories_ids(course, None, include_all=True)

    for cohorted_discussion_id in course_settings.cohorted_discussions:
        if cohorted_discussion_id in course_wide_discussions:
            cohorted_course_wide_discussions.append(cohorted_discussion_id)
        elif cohorted_discussion_id in all_discussions:
            cohorted_inline_discussions.append(cohorted_discussion_id)

    return cohorted_course_wide_discussions, cohorted_inline_discussions


@require_http_methods(("GET", "PATCH"))
@ensure_csrf_cookie
@expect_json
@login_required
def course_cohort_settings_handler(request, course_key_string):
    """
    The restful handler for cohort setting requests. Requires JSON.
    This will raise 404 if user is not staff.
    GET
        Returns the JSON representation of cohort settings for the course.
    PATCH
        Updates the cohort settings for the course. Returns the JSON representation of updated settings.
    """
    course_key = CourseKey.from_string(course_key_string)
    course = get_course_with_access(request.user, 'staff', course_key)
    cohort_settings = cohorts.get_course_cohort_settings(course_key)

    if request.method == 'PATCH':
        cohorted_course_wide_discussions, cohorted_inline_discussions = get_cohorted_discussions(
            course, cohort_settings
        )

        settings_to_change = {}

        if 'is_cohorted' in request.json:
            settings_to_change['is_cohorted'] = request.json.get('is_cohorted')

        if 'cohorted_course_wide_discussions' in request.json or 'cohorted_inline_discussions' in request.json:
            cohorted_course_wide_discussions = request.json.get(
                'cohorted_course_wide_discussions', cohorted_course_wide_discussions
            )
            cohorted_inline_discussions = request.json.get(
                'cohorted_inline_discussions', cohorted_inline_discussions
            )
            settings_to_change['cohorted_discussions'] = cohorted_course_wide_discussions + cohorted_inline_discussions

        if 'always_cohort_inline_discussions' in request.json:
            settings_to_change['always_cohort_inline_discussions'] = request.json.get(
                'always_cohort_inline_discussions'
            )

        if not settings_to_change:
            return JsonResponse({"error": unicode("Bad Request")}, 400)

        try:
            cohort_settings = cohorts.set_course_cohort_settings(
                course_key, **settings_to_change
            )
        except ValueError as err:
            # Note: error message not translated because it is not exposed to the user (UI prevents this state).
            return JsonResponse({"error": unicode(err)}, 400)

    return JsonResponse(_get_course_cohort_settings_representation(course, cohort_settings))


@require_http_methods(("GET", "PUT", "POST", "PATCH"))
@ensure_csrf_cookie
@expect_json
@login_required
def cohort_handler(request, course_key_string, cohort_id=None):
    """
    The restful handler for cohort requests. Requires JSON.
    GET
        If a cohort ID is specified, returns a JSON representation of the cohort
            (name, id, user_count, assignment_type, user_partition_id, group_id).
        If no cohort ID is specified, returns the JSON representation of all cohorts.
           This is returned as a dict with the list of cohort information stored under the
           key `cohorts`.
    PUT or POST or PATCH
        If a cohort ID is specified, updates the cohort with the specified ID. Currently the only
        properties that can be updated are `name`, `user_partition_id` and `group_id`.
        Returns the JSON representation of the updated cohort.
        If no cohort ID is specified, creates a new cohort and returns the JSON representation of the updated
        cohort.
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_key_string)
    course = get_course_with_access(request.user, 'staff', course_key)
    if request.method == 'GET':
        if not cohort_id:
            all_cohorts = [
                _get_cohort_representation(c, course)
                for c in cohorts.get_course_cohorts(course)
            ]
            return JsonResponse({'cohorts': all_cohorts})
        else:
            cohort = cohorts.get_cohort_by_id(course_key, cohort_id)
            return JsonResponse(_get_cohort_representation(cohort, course))
    else:
        name = request.json.get('name')
        assignment_type = request.json.get('assignment_type')
        if not name:
            # Note: error message not translated because it is not exposed to the user (UI prevents this state).
            return JsonResponse({"error": "Cohort name must be specified."}, 400)
        if not assignment_type:
            # Note: error message not translated because it is not exposed to the user (UI prevents this state).
            return JsonResponse({"error": "Assignment type must be specified."}, 400)
        # If cohort_id is specified, update the existing cohort. Otherwise, create a new cohort.
        if cohort_id:
            cohort = cohorts.get_cohort_by_id(course_key, cohort_id)
            if name != cohort.name:
                if cohorts.is_cohort_exists(course_key, name):
                    err_msg = ugettext("A cohort with the same name already exists.")
                    return JsonResponse({"error": unicode(err_msg)}, 400)
                cohort.name = name
                cohort.save()
            try:
                cohorts.set_assignment_type(cohort, assignment_type)
            except ValueError as err:
                return JsonResponse({"error": unicode(err)}, 400)
        else:
            try:
                cohort = cohorts.add_cohort(course_key, name, assignment_type)
            except ValueError as err:
                return JsonResponse({"error": unicode(err)}, 400)

        group_id = request.json.get('group_id')
        if group_id is not None:
            user_partition_id = request.json.get('user_partition_id')
            if user_partition_id is None:
                # Note: error message not translated because it is not exposed to the user (UI prevents this state).
                return JsonResponse(
                    {"error": "If group_id is specified, user_partition_id must also be specified."}, 400
                )
            existing_group_id, existing_partition_id = cohorts.get_group_info_for_cohort(cohort)
            if group_id != existing_group_id or user_partition_id != existing_partition_id:
                unlink_cohort_partition_group(cohort)
                link_cohort_to_partition_group(cohort, user_partition_id, group_id)
        else:
            # If group_id was specified as None, unlink the cohort if it previously was associated with a group.
            existing_group_id, _ = cohorts.get_group_info_for_cohort(cohort)
            if existing_group_id is not None:
                unlink_cohort_partition_group(cohort)

        return JsonResponse(_get_cohort_representation(cohort, course))


@ensure_csrf_cookie
def users_in_cohort(request, course_key_string, cohort_id):
    """
    Return users in the cohort.  Show up to 100 per page, and page
    using the 'page' GET attribute in the call.  Format:

    Returns:
        Json dump of dictionary in the following format:
        {'success': True,
         'page': page,
         'num_pages': paginator.num_pages,
         'users': [{'username': ..., 'email': ..., 'name': ...}]
    }
    """
    # this is a string when we get it here
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_key_string)

    get_course_with_access(request.user, 'staff', course_key)

    # this will error if called with a non-int cohort_id.  That's ok--it
    # shouldn't happen for valid clients.
    cohort = cohorts.get_cohort_by_id(course_key, int(cohort_id))

    paginator = Paginator(cohort.users.all(), 100)
    try:
        page = int(request.GET.get('page'))
    except (TypeError, ValueError):
        # These strings aren't user-facing so don't translate them
        return HttpResponseBadRequest('Requested page must be numeric')
    else:
        if page < 0:
            return HttpResponseBadRequest('Requested page must be greater than zero')

    try:
        users = paginator.page(page)
    except EmptyPage:
        users = []  # When page > number of pages, return a blank page

    user_info = [{'username': u.username,
                  'email': u.email,
                  'name': '{0} {1}'.format(u.first_name, u.last_name)}
                 for u in users]

    return json_http_response({'success': True,
                               'page': page,
                               'num_pages': paginator.num_pages,
                               'users': user_info})


@transaction.non_atomic_requests
@ensure_csrf_cookie
@require_POST
def add_users_to_cohort(request, course_key_string, cohort_id):
    """
    Return json dict of:

    {'success': True,
     'added': [{'username': ...,
                'name': ...,
                'email': ...}, ...],
     'changed': [{'username': ...,
                  'name': ...,
                  'email': ...,
                  'previous_cohort': ...}, ...],
     'present': [str1, str2, ...],    # already there
     'unknown': [str1, str2, ...]}

     Raises Http404 if the cohort cannot be found for the given course.
    """
    # this is a string when we get it here
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_key_string)
    get_course_with_access(request.user, 'staff', course_key)

    try:
        cohort = cohorts.get_cohort_by_id(course_key, cohort_id)
    except CourseUserGroup.DoesNotExist:
        raise Http404("Cohort (ID {cohort_id}) not found for {course_key_string}".format(
            cohort_id=cohort_id,
            course_key_string=course_key_string
        ))

    users = request.POST.get('users', '')
    added = []
    changed = []
    present = []
    unknown = []
    for username_or_email in split_by_comma_and_whitespace(users):
        if not username_or_email:
            continue

        try:
            (user, previous_cohort) = cohorts.add_user_to_cohort(cohort, username_or_email)
            info = {
                'username': user.username,
                'email': user.email,
            }
            if previous_cohort:
                info['previous_cohort'] = previous_cohort
                changed.append(info)
            else:
                added.append(info)
        except ValueError:
            present.append(username_or_email)
        except User.DoesNotExist:
            unknown.append(username_or_email)

    return json_http_response({'success': True,
                               'added': added,
                               'changed': changed,
                               'present': present,
                               'unknown': unknown})


@ensure_csrf_cookie
@require_POST
def remove_user_from_cohort(request, course_key_string, cohort_id):
    """
    Expects 'username': username in POST data.

    Return json dict of:

    {'success': True} or
    {'success': False,
     'msg': error_msg}
    """
    # this is a string when we get it here
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_key_string)
    get_course_with_access(request.user, 'staff', course_key)

    username = request.POST.get('username')
    if username is None:
        return json_http_response({'success': False,
                                   'msg': 'No username specified'})

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        log.debug('no user')
        return json_http_response({'success': False,
                                   'msg': "No user '{0}'".format(username)})

    try:
        membership = CohortMembership.objects.get(user=user, course_id=course_key)
        membership.delete()

    except CohortMembership.DoesNotExist:
        pass

    return json_http_response({'success': True})


def debug_cohort_mgmt(request, course_key_string):
    """
    Debugging view for dev.
    """
    # this is a string when we get it here
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_key_string)
    # add staff check to make sure it's safe if it's accidentally deployed.
    get_course_with_access(request.user, 'staff', course_key)

    context = {'cohorts_url': reverse(
        'cohorts',
        kwargs={'course_key': course_key.to_deprecated_string()}
    )}
    return render_to_response('/course_groups/debug.html', context)


@expect_json
@login_required
def cohort_discussion_topics(request, course_key_string):
    """
    The handler for cohort discussion categories requests.
    This will raise 404 if user is not staff.

    Returns the JSON representation of discussion topics w.r.t categories for the course.

    Example:
        >>> example = {
        >>>               "course_wide_discussions": {
        >>>                   "entries": {
        >>>                       "General": {
        >>>                           "sort_key": "General",
        >>>                           "is_cohorted": True,
        >>>                           "id": "i4x-edx-eiorguegnru-course-foobarbaz"
        >>>                       }
        >>>                   }
        >>>                   "children": ["General", "entry"]
        >>>               },
        >>>               "inline_discussions" : {
        >>>                   "subcategories": {
        >>>                       "Getting Started": {
        >>>                           "subcategories": {},
        >>>                           "children": [
        >>>                               ["Working with Videos", "entry"],
        >>>                               ["Videos on edX", "entry"]
        >>>                           ],
        >>>                           "entries": {
        >>>                               "Working with Videos": {
        >>>                                   "sort_key": None,
        >>>                                   "is_cohorted": False,
        >>>                                   "id": "d9f970a42067413cbb633f81cfb12604"
        >>>                               },
        >>>                               "Videos on edX": {
        >>>                                   "sort_key": None,
        >>>                                   "is_cohorted": False,
        >>>                                   "id": "98d8feb5971041a085512ae22b398613"
        >>>                               }
        >>>                           }
        >>>                       },
        >>>                       "children": ["Getting Started", "subcategory"]
        >>>                   },
        >>>               }
        >>>          }
    """
    course_key = CourseKey.from_string(course_key_string)
    course = get_course_with_access(request.user, 'staff', course_key)

    discussion_topics = {}
    discussion_category_map = get_discussion_category_map(
        course, request.user, cohorted_if_in_list=True, exclude_unstarted=False
    )

    # We extract the data for the course wide discussions from the category map.
    course_wide_entries = discussion_category_map.pop('entries')

    course_wide_children = []
    inline_children = []

    for name, c_type in discussion_category_map['children']:
        if name in course_wide_entries and c_type == TYPE_ENTRY:
            course_wide_children.append([name, c_type])
        else:
            inline_children.append([name, c_type])

    discussion_topics['course_wide_discussions'] = {
        'entries': course_wide_entries,
        'children': course_wide_children
    }

    discussion_category_map['children'] = inline_children
    discussion_topics['inline_discussions'] = discussion_category_map

    return JsonResponse(discussion_topics)
