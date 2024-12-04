"""
Views related to operations on course objects
"""
import copy
import json
import logging
import random
import re
import string
from typing import Dict

import django.utils
from ccx_keys.locator import CCXLocator
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import FieldError, PermissionDenied, ValidationError as DjangoValidationError
from django.db.models import QuerySet
from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods
from edx_django_utils.monitoring import function_trace
from edx_toggles.toggles import WaffleSwitch
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import BlockUsageLocator
from organizations.api import add_organization_course, ensure_organization
from organizations.exceptions import InvalidOrganizationException
from rest_framework.exceptions import ValidationError

from cms.djangoapps.contentstore.xblock_storage_handlers.view_handlers import create_xblock_info
from cms.djangoapps.course_creators.views import add_user_with_status_unrequested, get_course_creator_status
from cms.djangoapps.course_creators.models import CourseCreator
from cms.djangoapps.models.settings.course_grading import CourseGradingModel
from cms.djangoapps.models.settings.course_metadata import CourseMetadata
from cms.djangoapps.models.settings.encoder import CourseSettingsEncoder
from cms.djangoapps.contentstore.api.views.utils import get_bool_param
from common.djangoapps.course_action_state.managers import CourseActionStateItemNotFoundError
from common.djangoapps.course_action_state.models import CourseRerunState, CourseRerunUIStateManager
from common.djangoapps.edxmako.shortcuts import render_to_response
from common.djangoapps.student.auth import (
    has_course_author_access,
    has_studio_read_access,
    has_studio_write_access,
    has_studio_advanced_settings_access,
    is_content_creator,
)
from common.djangoapps.student.roles import (
    CourseInstructorRole,
    CourseStaffRole,
    GlobalStaff,
    UserBasedRole,
    OrgStaffRole,
)
from common.djangoapps.util.json_request import JsonResponse, JsonResponseBadRequest, expect_json
from common.djangoapps.util.string_utils import _has_non_ascii_characters
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.credit.tasks import update_credit_course_requirements
from openedx.core.djangoapps.models.course_details import CourseDetails
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangolib.js_utils import dump_js_escaped_json
from openedx.core.lib.course_tabs import CourseTabPluginManager
from organizations.models import Organization
from xmodule.contentstore.content import StaticContent  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.course_block import CourseBlock, CourseFields  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.error_block import ErrorBlock  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore import EdxJSONEncoder  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.exceptions import DuplicateCourseError  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.tabs import CourseTab, CourseTabList, InvalidTabsException  # lint-amnesty, pylint: disable=wrong-import-order

from ..course_group_config import (
    COHORT_SCHEME,
    RANDOM_SCHEME,
    GroupConfiguration,
    GroupConfigurationsValidationError
)
from ..course_info_model import delete_course_update, get_course_updates, update_course_updates
from ..courseware_index import CoursewareSearchIndexer, SearchIndexingError
from ..tasks import rerun_course as rerun_course_task
from ..toggles import (
    default_enable_flexible_peer_openassessments,
    use_new_course_outline_page,
    use_new_home_page,
    use_new_updates_page,
    use_new_advanced_settings_page,
    use_new_grading_page,
    use_new_textbooks_page,
    use_new_group_configurations_page,
    use_new_schedule_details_page
)
from ..utils import (
    add_instructor,
    get_advanced_settings_url,
    get_course_grading,
    get_course_index_context,
    get_course_outline_url,
    get_course_rerun_context,
    get_course_settings,
    get_grading_url,
    get_group_configurations_context,
    get_group_configurations_url,
    get_home_context,
    get_library_context,
    get_lms_link_for_item,
    get_proctored_exam_settings_url,
    get_schedule_details_url,
    get_studio_home_url,
    get_updates_url,
    get_textbooks_context,
    get_textbooks_url,
    initialize_permissions,
    remove_all_instructors,
    reverse_course_url,
    reverse_library_url,
    reverse_url,
    reverse_usage_url,
    update_course_details,
    update_course_discussions_settings,
)
from .component import ADVANCED_COMPONENT_TYPES

log = logging.getLogger(__name__)
User = get_user_model()

__all__ = ['course_info_handler', 'course_handler', 'course_listing',
           'course_info_update_handler', 'course_search_index_handler',
           'course_rerun_handler',
           'settings_handler',
           'library_listing',
           'grading_handler',
           'advanced_settings_handler',
           'course_notifications_handler',
           'textbooks_list_handler', 'textbooks_detail_handler',
           'group_configurations_list_handler', 'group_configurations_detail_handler',
           'get_course_and_check_access']

WAFFLE_NAMESPACE = 'studio_home'
ENABLE_GLOBAL_STAFF_OPTIMIZATION = WaffleSwitch(  # lint-amnesty, pylint: disable=toggle-missing-annotation
    f'{WAFFLE_NAMESPACE}.enable_global_staff_optimization', __name__
)


class AccessListFallback(Exception):
    """
    An exception that is raised whenever we need to `fall back` to fetching *all* courses
    available to a user, rather than using a shorter method (i.e. fetching by group)
    """
    pass  # lint-amnesty, pylint: disable=unnecessary-pass


def get_course_and_check_access(course_key, user, depth=0):
    """
    Function used to calculate and return the locator and course block
    for the view functions in this file.
    """
    if not has_studio_read_access(user, course_key):
        raise PermissionDenied()
    course_block = modulestore().get_course(course_key, depth=depth)
    return course_block


def reindex_course_and_check_access(course_key, user):
    """
    Internal method used to restart indexing on a course.
    """
    if not has_course_author_access(user, course_key):
        raise PermissionDenied()
    return CoursewareSearchIndexer.do_course_reindex(modulestore(), course_key)


@login_required
def course_notifications_handler(request, course_key_string=None, action_state_id=None):
    """
    Handle incoming requests for notifications in a RESTful way.

    course_key_string and action_state_id must both be set; else a HttpBadResponseRequest is returned.

    For each of these operations, the requesting user must have access to the course;
    else a PermissionDenied error is returned.

    GET
        json: return json representing information about the notification (action, state, etc)
    DELETE
        json: return json repressing success or failure of dismissal/deletion of the notification
    PUT
        Raises a NotImplementedError.
    POST
        Raises a NotImplementedError.
    """
    # ensure that we have a course and an action state
    if not course_key_string or not action_state_id:
        return HttpResponseBadRequest()

    response_format = request.GET.get('format') or request.POST.get('format') or 'html'

    course_key = CourseKey.from_string(course_key_string)

    if response_format == 'json' or 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json'):
        if not has_studio_write_access(request.user, course_key):
            raise PermissionDenied()
        if request.method == 'GET':
            return _course_notifications_json_get(action_state_id)
        elif request.method == 'DELETE':
            # we assume any delete requests dismiss actions from the UI
            return _dismiss_notification(request, action_state_id)
        elif request.method == 'PUT':
            raise NotImplementedError()
        elif request.method == 'POST':
            raise NotImplementedError()
        else:
            return HttpResponseBadRequest()
    else:
        return HttpResponseNotFound()


def _course_notifications_json_get(course_action_state_id):
    """
    Return the action and the action state for the given id
    """
    try:
        action_state = CourseRerunState.objects.find_first(id=course_action_state_id)
    except CourseActionStateItemNotFoundError:
        return HttpResponseBadRequest()

    action_state_info = {
        'action': action_state.action,
        'state': action_state.state,
        'should_display': action_state.should_display
    }
    return JsonResponse(action_state_info)


def _dismiss_notification(request, course_action_state_id):
    """
    Update the display of the course notification
    """
    try:
        action_state = CourseRerunState.objects.find_first(id=course_action_state_id)

    except CourseActionStateItemNotFoundError:
        # Can't dismiss a notification that doesn't exist in the first place
        return HttpResponseBadRequest()

    if action_state.state == CourseRerunUIStateManager.State.FAILED:
        # We remove all permissions for this course key at this time, since
        # no further access is required to a course that failed to be created.
        remove_all_instructors(action_state.course_key)

    # The CourseRerunState is no longer needed by the UI; delete
    action_state.delete()

    return JsonResponse({'success': True})


@login_required
def course_handler(request, course_key_string=None):
    """
    The restful handler for course specific requests.
    It provides the course tree with the necessary information for identifying and labeling the parts. The root
    will typically be a 'course' object but may not be especially as we support blocks.

    GET
        html: return course listing page if not given a course id
        html: return html page overview for the given course if given a course id
        json: return json representing the course branch's index entry as well as dag w/ all of the children
        replaced w/ json docs where each doc has {'_id': , 'display_name': , 'children': }
    POST
        json: create a course, return resulting json
        descriptor (same as in GET course/...). Leaving off /branch/draft would imply create the course w/ default
        branches. Cannot change the structure contents ('_id', 'display_name', 'children') but can change the
        index entry.
    PUT
        json: update this course (index entry not xblock) such as repointing head, changing display name, org,
        course, run. Return same json as above.
    DELETE
        json: delete this branch from this course (leaving off /branch/draft would imply delete the course)
    """
    try:
        if course_key_string:
            course_key = CourseKey.from_string(course_key_string)
            if course_key.deprecated:
                logging.error(f"User {request.user.id} tried to access Studio for Old Mongo course {course_key}.")
                return HttpResponseNotFound()
        response_format = request.GET.get('format') or request.POST.get('format') or 'html'
        if response_format == 'json' or 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json'):
            if request.method == 'GET':
                course_key = CourseKey.from_string(course_key_string)
                with modulestore().bulk_operations(course_key):
                    course_block = get_course_and_check_access(course_key, request.user, depth=None)
                    return JsonResponse(_course_outline_json(request, course_block))
            elif request.method == 'POST':  # not sure if this is only post. If one will have ids, it goes after access
                return _create_or_rerun_course(request)
            elif not has_studio_write_access(request.user, CourseKey.from_string(course_key_string)):
                raise PermissionDenied()
            elif request.method == 'PUT':
                raise NotImplementedError()
            elif request.method == 'DELETE':
                raise NotImplementedError()
            else:
                return HttpResponseBadRequest()
        elif request.method == 'GET':  # assume html
            if course_key_string is None:
                return redirect(reverse('home'))
            else:
                return course_index(request, CourseKey.from_string(course_key_string))
        else:
            return HttpResponseNotFound()
    except InvalidKeyError:
        raise Http404  # lint-amnesty, pylint: disable=raise-missing-from


@login_required
@ensure_csrf_cookie
@require_http_methods(["GET"])
def course_rerun_handler(request, course_key_string):
    """
    The restful handler for course reruns.
    GET
        html: return html page with form to rerun a course for the given course id
    """
    # Only global staff (PMs) are able to rerun courses during the soft launch
    if not GlobalStaff().has_user(request.user):
        raise PermissionDenied()
    course_key = CourseKey.from_string(course_key_string)
    with modulestore().bulk_operations(course_key):
        course_block = get_course_and_check_access(course_key, request.user, depth=3)
        if request.method == 'GET':
            course_rerun_context = get_course_rerun_context(course_key, course_block, request.user)
            return render_to_response('course-create-rerun.html', course_rerun_context)


@login_required
@ensure_csrf_cookie
@require_GET
def course_search_index_handler(request, course_key_string):
    """
    The restful handler for course indexing.
    GET
        html: return status of indexing task
        json: return status of indexing task
    """
    # Only global staff (PMs) are able to index courses
    if not GlobalStaff().has_user(request.user):
        raise PermissionDenied()
    course_key = CourseKey.from_string(course_key_string)
    content_type = request.META.get('CONTENT_TYPE', None)
    if content_type is None:
        content_type = "application/json; charset=utf-8"
    with modulestore().bulk_operations(course_key):
        try:
            reindex_course_and_check_access(course_key, request.user)
        except SearchIndexingError as search_err:
            return HttpResponse(dump_js_escaped_json({
                "user_message": search_err.error_list
            }), content_type=content_type, status=500)
        return HttpResponse(dump_js_escaped_json({
            "user_message": _("Course has been successfully reindexed.")
        }), content_type=content_type, status=200)


def _course_outline_json(request, course_block):
    """
    Returns a JSON representation of the course block and recursively all of its children.
    """
    is_concise = request.GET.get('format') == 'concise'
    include_children_predicate = lambda xblock: not xblock.category == 'vertical'
    if is_concise:
        include_children_predicate = lambda xblock: xblock.has_children
    return create_xblock_info(
        course_block,
        include_child_info=True,
        course_outline=False if is_concise else True,  # lint-amnesty, pylint: disable=simplifiable-if-expression
        include_children_predicate=include_children_predicate,
        is_concise=is_concise,
        user=request.user
    )


def get_in_process_course_actions(request):
    """
     Get all in-process course actions
    """
    return [
        course for course in
        CourseRerunState.objects.find_all(
            exclude_args={'state': CourseRerunUIStateManager.State.SUCCEEDED},
            should_display=True,
        )
        if has_studio_read_access(request.user, course.course_key)
    ]


def _accessible_courses_summary_iter(request, org=None):
    """
    List all courses available to the logged in user by iterating through all the courses

    Arguments:
        request: the request object
        org (string): if not None, this value will limit the courses returned. An empty
            string will result in no courses, and otherwise only courses with the
            specified org will be returned. The default value is None.
    """
    def course_filter(course_summary):
        """
        Filter out unusable and inaccessible courses
        """
        # TODO remove this condition when templates purged from db
        if course_summary.location.course == 'templates':
            return False

        return has_studio_read_access(request.user, course_summary.id)

    enable_home_page_api_v2 = settings.FEATURES["ENABLE_HOME_PAGE_COURSE_API_V2"]

    if org is not None:
        courses_summary = [] if org == '' else CourseOverview.get_all_courses(orgs=[org])
    elif enable_home_page_api_v2:
        # If the new home page API is enabled, we should use the Django ORM to filter and order the courses
        courses_summary = CourseOverview.get_all_courses()
    else:
        courses_summary = modulestore().get_course_summaries()

    if enable_home_page_api_v2:
        search_query, order, active_only, archived_only = get_query_params_if_present(request)
        courses_summary = get_filtered_and_ordered_courses(
            courses_summary,
            active_only,
            archived_only,
            search_query,
            order,
        )

    courses_summary = filter(course_filter, courses_summary)
    in_process_course_actions = get_in_process_course_actions(request)

    return courses_summary, in_process_course_actions


def get_query_params_if_present(request):
    """
    Returns the query params from request if present.

    Arguments:
        request: the request object

    Returns:
        search_query (str): any string used to filter Course Overviews based on visible fields.
        order (str): any string used to order Course Overviews.
        active_only (str): if not None, this value will limit the courses returned to active courses.
            The default value is None.
        archived_only (str): if not None, this value will limit the courses returned to archived courses.
            The default value is None.
    """
    allowed_query_params = ['search', 'order', 'active_only', 'archived_only']
    if not any(param in request.GET for param in allowed_query_params):
        return None, None, None, None
    search_query = request.GET.get('search')
    order = request.GET.get('order')
    active_only = get_bool_param(request, 'active_only', None)
    archived_only = get_bool_param(request, 'archived_only', None)
    return search_query, order, active_only, archived_only


def get_filtered_and_ordered_courses(course_overviews, active_only, archived_only, search_query, order):
    """
    Returns the filtered and ordered courses based on the query params.

    Arguments:
        courses_summary (Course Overview objects): course overview queryset to be filtered.
        active_only (str): if not None, this value will limit the courses returned to active courses.
            The default value is None.
        archived_only (str): if not None, this value will limit the courses returned to archived courses.
            The default value is None.
        search_query (str): any string used to filter Course Overviews based on visible fields.
        order (str): any string used to order Course Overviews.

    Returns:
        Course Overview objects: queryset filtered and ordered based on the query params.
    """
    course_overviews = get_courses_by_status(active_only, archived_only, course_overviews)
    course_overviews = get_courses_by_search_query(search_query, course_overviews)
    course_overviews = get_courses_order_by(order, course_overviews)
    return course_overviews


def _accessible_courses_iter(request):
    """
    List all courses available to the logged in user by iterating through all the courses.
    """
    def course_filter(course):
        """
        Filter out unusable and inaccessible courses
        """
        if isinstance(course, ErrorBlock):
            return False

        # Custom Courses for edX (CCX) is an edX feature for re-using course content.
        # CCXs cannot be edited in Studio (aka cms) and should not be shown in this dashboard.
        if isinstance(course.id, CCXLocator):
            return False

        # TODO remove this condition when templates purged from db
        if course.location.course == 'templates':
            return False

        return has_studio_read_access(request.user, course.id)

    courses = filter(course_filter, modulestore().get_courses())

    in_process_course_actions = get_in_process_course_actions(request)
    return courses, in_process_course_actions


def _accessible_courses_iter_for_tests(request):
    """
    List all courses available to the logged in user by iterating through all the courses.
    CourseSummary objects are used for listing purposes.
    This method is only used by tests.
    """
    def course_filter(course):
        """
        Filter out unusable and inaccessible courses
        """

        # Custom Courses for edX (CCX) is an edX feature for re-using course content.
        # CCXs cannot be edited in Studio (aka cms) and should not be shown in this dashboard.
        if isinstance(course.id, CCXLocator):
            return False

        # TODO remove this condition when templates purged from db
        if course.location.course == 'templates':
            return False

        return has_studio_read_access(request.user, course.id)

    courses = filter(course_filter, CourseOverview.get_all_courses())

    in_process_course_actions = get_in_process_course_actions(request)
    return courses, in_process_course_actions


def _accessible_courses_list_from_groups(request):
    """
    List all courses available to the logged in user by reversing access group names
    """
    def filter_ccx(course_access):
        """ CCXs cannot be edited in Studio and should not be shown in this dashboard """
        return not isinstance(course_access.course_id, CCXLocator)

    instructor_courses = UserBasedRole(request.user, CourseInstructorRole.ROLE).courses_with_role()
    staff_courses = UserBasedRole(request.user, CourseStaffRole.ROLE).courses_with_role()
    all_courses = list(filter(filter_ccx, instructor_courses | staff_courses))
    courses_list = []
    course_keys = {}

    user_global_orgs = set()
    for course_access in all_courses:
        if course_access.course_id is not None:
            course_keys[course_access.course_id] = course_access.course_id
        elif course_access.org:
            user_global_orgs.add(course_access.org)
        else:
            raise AccessListFallback

    if user_global_orgs:
        # Getting courses from user global orgs
        overviews = CourseOverview.get_all_courses(orgs=list(user_global_orgs))
        overviews_course_keys = {overview.id: overview.id for overview in overviews}
        course_keys.update(overviews_course_keys)

    course_keys = list(course_keys.values())

    if course_keys:
        courses_list = CourseOverview.get_all_courses(filter_={'id__in': course_keys})
    else:
        # If no course keys are found for the current user, then return without filtering
        # or ordering the courses list.
        return courses_list, []

    search_query, order, active_only, archived_only = get_query_params_if_present(request)
    courses_list = get_filtered_and_ordered_courses(
        courses_list,
        active_only,
        archived_only,
        search_query,
        order,
    )

    return courses_list, []


def get_courses_by_status(
    active_only: bool,
    archived_only: bool,
    course_overviews: QuerySet[CourseOverview]
) -> QuerySet[CourseOverview]:
    """
    Return course overviews based on a base queryset filtered by a status.

    Args:
        active_only (str): if not None, this value will limit the courses returned to active courses.
            The default value is None.
        archived_only (str): if not None, this value will limit the courses returned to archived courses.
            The default value is None.
        course_overviews (Course Overview objects): course overview queryset to be filtered.
    """
    return CourseOverview.get_courses_by_status(active_only, archived_only, course_overviews)


def get_courses_by_search_query(
    search_query: str | None,
    course_overviews: QuerySet[CourseOverview]
) -> QuerySet[CourseOverview]:
    """Return course overviews based on a base queryset filtered by a search query.

    Args:
        search_query (str): any string used to filter Course Overviews based on visible fields.
        course_overviews (Course Overview objects): course overview queryset to be filtered.
    """
    if not search_query:
        return course_overviews
    return CourseOverview.get_courses_matching_query(search_query, course_overviews=course_overviews)


def get_courses_order_by(
    order_query: str | None,
    course_overviews: QuerySet[CourseOverview]
) -> QuerySet[CourseOverview]:
    """Return course overviews based on a base queryset ordered by a query.

    Args:
        order_query (str): any string used to order Course Overviews.
        course_overviews (Course Overview objects): queryset to be ordered.
    """
    if not order_query:
        return course_overviews
    try:
        return course_overviews.order_by(order_query)
    except FieldError as e:
        log.exception(f"Error ordering courses by {order_query}: {e}")
        return course_overviews


@function_trace('_accessible_libraries_iter')
def _accessible_libraries_iter(user, org=None):
    """
    List all libraries available to the logged in user by iterating through all libraries.

    org (string): if not None, this value will limit the libraries returned. An empty
        string will result in no libraries, and otherwise only libraries with the
        specified org will be returned. The default value is None.
    """
    if org is not None:
        libraries = [] if org == '' else modulestore().get_libraries(org=org)
    else:
        libraries = modulestore().get_library_summaries()
    # No need to worry about ErrorBlocks - split's get_libraries() never returns them.
    return (lib for lib in libraries if has_studio_read_access(user, lib.location.library_key))


@login_required
@ensure_csrf_cookie
def course_listing(request):
    """
    List all courses and libraries available to the logged in user
    """
    if use_new_home_page():
        return redirect(get_studio_home_url())

    home_context = get_home_context(request)
    return render_to_response('index.html', home_context)


@login_required
@ensure_csrf_cookie
def library_listing(request):
    """
    List all Libraries available to the logged in user
    """
    data = get_library_context(request)
    return render_to_response('index.html', data)


def _format_library_for_view(library, request):
    """
    Return a dict of the data which the view requires for each library
    """

    return {
        'display_name': library.display_name,
        'library_key': str(library.location.library_key),
        'url': reverse_library_url('library_handler', str(library.location.library_key)),
        'org': library.display_org_with_default,
        'number': library.display_number_with_default,
        'can_edit': has_studio_write_access(request.user, library.location.library_key),
    }


def _get_rerun_link_for_item(course_key):
    """ Returns the rerun link for the given course key. """
    return reverse_course_url('course_rerun_handler', course_key)


def _deprecated_blocks_info(course_block, deprecated_block_types):
    """
    Returns deprecation information about `deprecated_block_types`

    Arguments:
        course_block (CourseBlock): course object
        deprecated_block_types (list): list of deprecated blocks types

    Returns:
        Dict with following keys:
        deprecated_enabled_block_types (list): list containing all deprecated blocks types enabled on this course
        blocks (list): List of `deprecated_enabled_block_types` instances and their parent's url
        advance_settings_url (str): URL to advance settings page
    """
    data = {
        'deprecated_enabled_block_types': [
            block_type for block_type in course_block.advanced_modules if block_type in deprecated_block_types
        ],
        'blocks': [],
        'advance_settings_url': reverse_course_url('advanced_settings_handler', course_block.id)
    }

    deprecated_blocks = modulestore().get_items(
        course_block.id,
        qualifiers={
            'category': re.compile('^' + '$|^'.join(deprecated_block_types) + '$')
        }
    )

    for block in deprecated_blocks:
        data['blocks'].append([
            reverse_usage_url('container_handler', block.parent),
            block.display_name
        ])

    return data


@login_required
@ensure_csrf_cookie
def course_index(request, course_key):
    """
    Display an editable course overview.

    org, course, name: Attributes of the Location for the item to edit
    """
    if use_new_course_outline_page(course_key):
        return redirect(get_course_outline_url(course_key))
    with modulestore().bulk_operations(course_key):
        # A depth of None implies the whole course. The course outline needs this in order to compute has_changes.
        # A unit may not have a draft version, but one of its components could, and hence the unit itself has changes.
        course_block = get_course_and_check_access(course_key, request.user, depth=None)
        if not course_block:
            raise Http404
        # should be under bulk_operations if course_block is passed
        course_index_context = get_course_index_context(request, course_key, course_block)
        return render_to_response('course_outline.html', course_index_context)


@function_trace('get_courses_accessible_to_user')
def get_courses_accessible_to_user(request, org=None):
    """
    Try to get all courses by first reversing django groups and fallback to old method if it fails
    Note: overhead of pymongo reads will increase if getting courses from django groups fails

    Arguments:
        request: the request object
        org (string): for global staff users ONLY, this value will be used to limit
            the courses returned. A value of None will have no effect (all courses
            returned), an empty string will result in no courses, and otherwise only courses with the
            specified org will be returned. The default value is None.
    """
    if GlobalStaff().has_user(request.user):
        # user has global access so no need to get courses from django groups
        courses, in_process_course_actions = _accessible_courses_summary_iter(request, org)
    else:
        try:
            courses, in_process_course_actions = _accessible_courses_list_from_groups(request)
        except AccessListFallback:
            # user have some old groups or there was some error getting courses from django groups
            # so fallback to iterating through all courses
            courses, in_process_course_actions = _accessible_courses_summary_iter(request)
    return courses, in_process_course_actions


def _process_courses_list(courses_iter, in_process_course_actions, split_archived=False):
    """
    Iterates over the list of courses to be displayed to the user, and:

    * Removes any in-process courses from the courses list. "In-process" refers to courses
      that are in the process of being generated for re-run.
    * If split_archived=True, removes any archived courses and returns them in a separate list.
      Archived courses have has_ended() == True.
    * Formats the returned courses (in both lists) to prepare them for rendering to the view.
    """
    def format_course_for_view(course):
        """
        Return a dict of the data which the view requires for each course
        """
        course_context = {
            'display_name': course.display_name,
            'course_key': str(course.location.course_key),
            'url': reverse_course_url('course_handler', course.id),
            'lms_link': get_lms_link_for_item(course.location),
            'rerun_link': _get_rerun_link_for_item(course.id),
            'org': course.display_org_with_default,
            'number': course.display_number_with_default,
            'run': course.location.run
        }
        if course.id.deprecated:
            course_context.update({
                'url': None,
                'lms_link': None,
                'rerun_link': None
            })
        return course_context

    in_process_action_course_keys = {uca.course_key for uca in in_process_course_actions}
    active_courses = []
    archived_courses = []

    for course in courses_iter:
        if isinstance(course, ErrorBlock) or (course.id in in_process_action_course_keys):
            continue

        formatted_course = format_course_for_view(course)
        if split_archived and course.has_ended():
            archived_courses.append(formatted_course)
        else:
            active_courses.append(formatted_course)

    return active_courses, archived_courses


def course_outline_initial_state(locator_to_show, course_structure):
    """
    Returns the desired initial state for the course outline view. If the 'show' request parameter
    was provided, then the view's initial state will be to have the desired item fully expanded
    and to scroll to see the new item.
    """
    def find_xblock_info(xblock_info, locator):
        """
        Finds the xblock info for the specified locator.
        """
        if xblock_info['id'] == locator:
            return xblock_info
        children = xblock_info['child_info']['children'] if xblock_info.get('child_info', None) else None
        if children:
            for child_xblock_info in children:
                result = find_xblock_info(child_xblock_info, locator)
                if result:
                    return result
        return None

    def collect_all_locators(locators, xblock_info):
        """
        Collect all the locators for an xblock and its children.
        """
        locators.append(xblock_info['id'])
        children = xblock_info['child_info']['children'] if xblock_info.get('child_info', None) else None
        if children:
            for child_xblock_info in children:
                collect_all_locators(locators, child_xblock_info)

    selected_xblock_info = find_xblock_info(course_structure, locator_to_show)
    if not selected_xblock_info:
        return None
    expanded_locators = []
    collect_all_locators(expanded_locators, selected_xblock_info)
    return {
        'locator_to_show': locator_to_show,
        'expanded_locators': expanded_locators
    }


@expect_json
def _create_or_rerun_course(request):
    """
    To be called by requests that create a new destination course (i.e., create_new_course and rerun_course)
    Returns the destination course_key and overriding fields for the new course.
    Raises DuplicateCourseError and InvalidKeyError
    """
    try:
        org = request.json.get('org')
        course = request.json.get('number', request.json.get('course'))
        display_name = request.json.get('display_name')
        # force the start date for reruns and allow us to override start via the client
        start = request.json.get('start', CourseFields.start.default)
        end = request.json.get('end', CourseFields.end.default)
        run = request.json.get('run')
        has_course_creator_role = is_content_creator(request.user, org)

        if not has_course_creator_role:
            raise PermissionDenied()

        # allow/disable unicode characters in course_id according to settings
        if not settings.FEATURES.get('ALLOW_UNICODE_COURSE_ID'):
            if _has_non_ascii_characters(org) or _has_non_ascii_characters(course) or _has_non_ascii_characters(run):
                return JsonResponse(
                    {'error': _('Special characters not allowed in organization, course number, and course run.')},
                    status=400
                )

        fields = {'start': start, 'end': end}
        if display_name is not None:
            fields['display_name'] = display_name

        # Set a unique wiki_slug for newly created courses. To maintain active wiki_slugs for
        # existing xml courses this cannot be changed in CourseBlock.
        # # TODO get rid of defining wiki slug in this org/course/run specific way and reconcile
        # w/ xmodule.course_block.CourseBlock.__init__
        wiki_slug = f"{org}.{course}.{run}"
        definition_data = {'wiki_slug': wiki_slug}
        fields.update(definition_data)

        source_course_key = request.json.get('source_course_key')
        if source_course_key:
            source_course_key = CourseKey.from_string(source_course_key)
            destination_course_key = rerun_course(request.user, source_course_key, org, course, run, fields)
            return JsonResponse({
                'url': reverse_url('course_handler'),
                'destination_course_key': str(destination_course_key)
            })
        else:
            try:
                new_course = create_new_course(request.user, org, course, run, fields)
                return JsonResponse({
                    'url': reverse_course_url('course_handler', new_course.id),
                    'course_key': str(new_course.id),
                })
            except ValidationError as ex:
                return JsonResponse({'error': str(ex)}, status=400)
    except DuplicateCourseError:
        return JsonResponse({
            'ErrMsg': _(
                'There is already a course defined with the same '
                'organization and course number. Please '
                'change either organization or course number to be unique.'
            ),
            'OrgErrMsg': _(
                'Please change either the organization or '
                'course number so that it is unique.'),
            'CourseErrMsg': _(
                'Please change either the organization or '
                'course number so that it is unique.'),
        })
    except InvalidKeyError as error:
        return JsonResponse({
            "ErrMsg": _("Unable to create course '{name}'.\n\n{err}").format(name=display_name, err=str(error))}
        )
    except PermissionDenied as error:  # pylint: disable=unused-variable
        log.info(
            "User does not have the permission to create course in this organization"
            "or course creation is disabled."
            "User: '%s' Org: '%s' Course #: '%s'.",
            request.user.id,
            org,
            course,
        )
        return JsonResponse({
            'error': _('User does not have the permission to create courses in this organization '
                       'or course creation is disabled')},
            status=403
        )


def create_new_course(user, org, number, run, fields):
    """
    Create a new course run.

    Raises:
        DuplicateCourseError: Course run already exists.
    """
    try:
        org_data = ensure_organization(org)
    except InvalidOrganizationException:
        raise ValidationError(_(  # lint-amnesty, pylint: disable=raise-missing-from
            'You must link this course to an organization in order to continue. Organization '
            'you selected does not exist in the system, you will need to add it to the system'
        ))
    store_for_new_course = modulestore().default_modulestore.get_modulestore_type()
    new_course = create_new_course_in_store(store_for_new_course, user, org, number, run, fields)
    add_organization_course(org_data, new_course.id)
    update_course_discussions_settings(new_course)

    # Enable certain fields rolling forward, where configured
    if default_enable_flexible_peer_openassessments(new_course.id):
        new_course.force_on_flexible_peer_openassessments = True
    modulestore().update_item(new_course, new_course.published_by)

    return new_course


def create_new_course_in_store(store, user, org, number, run, fields):
    """
    Create course in store w/ handling instructor enrollment, permissions, and defaulting the wiki slug.
    Separated out b/c command line course creation uses this as well as the web interface.
    """

    # Set default language from settings and enable web certs
    fields.update({
        'language': getattr(settings, 'DEFAULT_COURSE_LANGUAGE', 'en'),
        'cert_html_view_enabled': True,
    })

    with modulestore().default_store(store):
        # Creating the course raises DuplicateCourseError if an existing course with this org/name is found
        new_course = modulestore().create_course(
            org,
            number,
            run,
            user.id,
            fields=fields,
        )

    # Make sure user has instructor and staff access to the new course
    add_instructor(new_course.id, user, user)

    # Initialize permissions for user in the new course
    initialize_permissions(new_course.id, user)
    return new_course


def rerun_course(user, source_course_key, org, number, run, fields, background=True):
    """
    Rerun an existing course.
    """
    # verify user has access to the original course
    if not has_studio_write_access(user, source_course_key):
        raise PermissionDenied()

    # create destination course key
    store = modulestore()
    with store.default_store('split'):
        destination_course_key = store.make_course_key(org, number, run)

    # verify org course and run don't already exist
    if store.has_course(destination_course_key, ignore_case=True):
        raise DuplicateCourseError(source_course_key, destination_course_key)

    # if org or name of source course don't match the destination course,
    # verify user has access to the destination course
    if source_course_key.org != destination_course_key.org or source_course_key.course != destination_course_key.course:
        if not has_studio_write_access(user, destination_course_key):
            raise PermissionDenied()

    # Make sure user has instructor and staff access to the destination course
    # so the user can see the updated status for that course
    add_instructor(destination_course_key, user, user)

    # Mark the action as initiated
    CourseRerunState.objects.initiated(source_course_key, destination_course_key, user, fields['display_name'])

    # Clear the fields that must be reset for the rerun
    fields['advertised_start'] = None
    fields['enrollment_start'] = None
    fields['enrollment_end'] = None
    fields['video_upload_pipeline'] = {}

    # Enable certain fields rolling forward, where configured
    if default_enable_flexible_peer_openassessments(source_course_key):
        fields['force_on_flexible_peer_openassessments'] = True

    json_fields = json.dumps(fields, cls=EdxJSONEncoder)
    args = [str(source_course_key), str(destination_course_key), user.id, json_fields]

    if background:
        rerun_course_task.delay(*args)
    else:
        rerun_course_task(*args)

    return destination_course_key


@login_required
@ensure_csrf_cookie
@require_http_methods(["GET"])
def course_info_handler(request, course_key_string):
    """
    GET
        html: return html for editing the course info handouts and updates.
    """
    try:
        course_key = CourseKey.from_string(course_key_string)
    except InvalidKeyError:
        raise Http404  # lint-amnesty, pylint: disable=raise-missing-from

    with modulestore().bulk_operations(course_key):
        course_block = get_course_and_check_access(course_key, request.user)
        if not course_block:
            raise Http404
        if use_new_updates_page(course_key):
            return redirect(get_updates_url(course_key))
        if 'text/html' in request.META.get('HTTP_ACCEPT', 'text/html'):
            return render_to_response(
                'course_info.html',
                {
                    'context_course': course_block,
                    'updates_url': reverse_course_url('course_info_update_handler', course_key),
                    'handouts_locator': course_key.make_usage_key('course_info', 'handouts'),
                    'base_asset_url': StaticContent.get_base_url_path_for_course_assets(course_block.id),
                }
            )
        else:
            return HttpResponseBadRequest("Only supports html requests")


@login_required
@ensure_csrf_cookie
@require_http_methods(("GET", "POST", "PUT", "DELETE"))
@expect_json
def course_info_update_handler(request, course_key_string, provided_id=None):
    """
    restful CRUD operations on course_info updates.
    provided_id should be none if it's new (create) and index otherwise.
    GET
        json: return the course info update models
    POST
        json: create an update
    PUT or DELETE
        json: change an existing update
    """
    if 'application/json' not in request.META.get('HTTP_ACCEPT', 'application/json'):
        return HttpResponseBadRequest("Only supports json requests")

    course_key = CourseKey.from_string(course_key_string)
    usage_key = course_key.make_usage_key('course_info', 'updates')
    if provided_id == '':
        provided_id = None

    # check that logged in user has permissions to this item (GET shouldn't require this level?)
    if not has_studio_write_access(request.user, usage_key.course_key):
        raise PermissionDenied()

    if request.method == 'GET':
        course_updates = get_course_updates(usage_key, provided_id, request.user.id)
        if isinstance(course_updates, dict) and course_updates.get('error'):
            return JsonResponse(course_updates, course_updates.get('status', 400))
        else:
            return JsonResponse(course_updates)
    elif request.method == 'DELETE':
        try:
            return JsonResponse(delete_course_update(usage_key, request.json, provided_id, request.user))
        except:  # lint-amnesty, pylint: disable=bare-except
            return HttpResponseBadRequest(
                "Failed to delete",
                content_type="text/plain"
            )
    # can be either and sometimes django is rewriting one to the other:
    elif request.method in ('POST', 'PUT'):
        try:
            return JsonResponse(update_course_updates(
                usage_key, request.json, provided_id, request.user, request.method
            ))
        except:  # lint-amnesty, pylint: disable=bare-except
            return HttpResponseBadRequest(
                "Failed to save",
                content_type="text/plain"
            )


@login_required
@ensure_csrf_cookie
@require_http_methods(("GET", "PUT", "POST"))
@expect_json
def settings_handler(request, course_key_string):  # lint-amnesty, pylint: disable=too-many-statements
    """
    Course settings for dates and about pages
    GET
        html: get the page
        json: get the CourseDetails model
    PUT
        json: update the Course and About xblocks through the CourseDetails model
    """
    course_key = CourseKey.from_string(course_key_string)

    with modulestore().bulk_operations(course_key):
        course_block = get_course_and_check_access(course_key, request.user)
        if 'text/html' in request.META.get('HTTP_ACCEPT', '') and request.method == 'GET':
            if use_new_schedule_details_page(course_key):
                return redirect(get_schedule_details_url(course_key))
            settings_context = get_course_settings(request, course_key, course_block)
            return render_to_response('settings.html', settings_context)
        elif 'application/json' in request.META.get('HTTP_ACCEPT', ''):  # pylint: disable=too-many-nested-blocks
            if request.method == 'GET':
                course_details = CourseDetails.fetch(course_key)
                return JsonResponse(
                    course_details,
                    # encoder serializes dates, old locations, and instances
                    encoder=CourseSettingsEncoder
                )
            # For every other possible method type submitted by the caller...
            else:
                try:
                    update_data = update_course_details(request, course_key, request.json, course_block)
                except DjangoValidationError as err:
                    return JsonResponseBadRequest({"error": err.message})

                return JsonResponse(update_data, encoder=CourseSettingsEncoder)


@login_required
@ensure_csrf_cookie
@require_http_methods(("GET", "POST", "PUT", "DELETE"))
@expect_json
def grading_handler(request, course_key_string, grader_index=None):
    """
    Course Grading policy configuration
    GET
        html: get the page
        json no grader_index: get the CourseGrading model (graceperiod, cutoffs, and graders)
        json w/ grader_index: get the specific grader
    PUT
        json no grader_index: update the Course through the CourseGrading model
        json w/ grader_index: create or update the specific grader (create if index out of range)
    """
    course_key = CourseKey.from_string(course_key_string)
    with modulestore().bulk_operations(course_key):
        if not has_studio_read_access(request.user, course_key):
            raise PermissionDenied()

        if 'text/html' in request.META.get('HTTP_ACCEPT', '') and request.method == 'GET':
            if use_new_grading_page(course_key):
                return redirect(get_grading_url(course_key))
            grading_context = get_course_grading(course_key)
            return render_to_response('settings_graders.html', grading_context)
        elif 'application/json' in request.META.get('HTTP_ACCEPT', ''):
            if request.method == 'GET':
                if grader_index is None:
                    return JsonResponse(
                        CourseGradingModel.fetch(course_key),
                        # encoder serializes dates, old locations, and instances
                        encoder=CourseSettingsEncoder
                    )
                else:
                    return JsonResponse(CourseGradingModel.fetch_grader(course_key, grader_index))
            elif request.method in ('POST', 'PUT'):  # post or put, doesn't matter.
                # update credit course requirements if 'minimum_grade_credit'
                # field value is changed
                if 'minimum_grade_credit' in request.json:
                    update_credit_course_requirements.delay(str(course_key))

                # None implies update the whole model (cutoffs, graceperiod, and graders) not a specific grader
                if grader_index is None:
                    return JsonResponse(
                        CourseGradingModel.update_from_json(course_key, request.json, request.user),
                        encoder=CourseSettingsEncoder
                    )
                else:
                    return JsonResponse(
                        CourseGradingModel.update_grader_from_json(course_key, request.json, request.user)
                    )
            elif request.method == "DELETE" and grader_index is not None:
                CourseGradingModel.delete_grader(course_key, grader_index, request.user)
                return JsonResponse()


def _refresh_course_tabs(user: User, course_block: CourseBlock):
    """
    Automatically adds/removes tabs if changes to the course require them.

    Raises:
        InvalidTabsException: raised if there's a problem with the new version of the tabs.
    """

    def update_tab(tabs, tab_type, tab_enabled):
        """
        Adds or removes a course tab based upon whether it is enabled.
        """
        tab_panel = {
            "type": tab_type.type,
        }
        has_tab = tab_panel in tabs
        if tab_enabled and not has_tab:
            tabs.append(CourseTab.from_json(tab_panel))
        elif not tab_enabled and has_tab:
            tabs.remove(tab_panel)

    course_tabs = copy.copy(course_block.tabs)

    # Additionally update any tabs that are provided by non-dynamic course views
    for tab_type in CourseTabPluginManager.get_tab_types():
        if not tab_type.is_dynamic and tab_type.is_default:
            tab_enabled = tab_type.is_enabled(course_block, user=user)
            update_tab(course_tabs, tab_type, tab_enabled)

    CourseTabList.validate_tabs(course_tabs)

    # Save the tabs into the course if they have been changed
    if course_tabs != course_block.tabs:
        course_block.tabs = course_tabs


@login_required
@ensure_csrf_cookie
@require_http_methods(("GET", "POST", "PUT"))
@expect_json
def advanced_settings_handler(request, course_key_string):
    """
    Course settings configuration
    GET
        html: get the page
        json: get the model
    PUT, POST
        json: update the Course's settings. The payload is a json rep of the
            metadata dicts.
    """
    if not has_studio_advanced_settings_access(request.user):
        raise PermissionDenied()

    course_key = CourseKey.from_string(course_key_string)
    with modulestore().bulk_operations(course_key):
        course_block = get_course_and_check_access(course_key, request.user)

        advanced_dict = CourseMetadata.fetch(course_block)
        if settings.FEATURES.get('DISABLE_MOBILE_COURSE_AVAILABLE', False):
            advanced_dict.get('mobile_available')['deprecated'] = True

        if 'text/html' in request.META.get('HTTP_ACCEPT', '') and request.method == 'GET':
            if use_new_advanced_settings_page(course_key):
                return redirect(get_advanced_settings_url(course_key))
            publisher_enabled = configuration_helpers.get_value_for_org(
                course_block.location.org,
                'ENABLE_PUBLISHER',
                settings.FEATURES.get('ENABLE_PUBLISHER', False)
            )
            # gather any errors in the currently stored proctoring settings.
            proctoring_errors = CourseMetadata.validate_proctoring_settings(course_block, advanced_dict, request.user)

            return render_to_response('settings_advanced.html', {
                'context_course': course_block,
                'advanced_dict': advanced_dict,
                'advanced_settings_url': reverse_course_url('advanced_settings_handler', course_key),
                'publisher_enabled': publisher_enabled,
                'mfe_proctored_exam_settings_url': get_proctored_exam_settings_url(course_block.id),
                'proctoring_errors': proctoring_errors,
            })
        elif 'application/json' in request.META.get('HTTP_ACCEPT', ''):
            if request.method == 'GET':
                return JsonResponse(CourseMetadata.fetch(course_block))
            else:
                try:
                    return JsonResponse(
                        update_course_advanced_settings(course_block, request.json, request.user)
                    )
                except ValidationError as err:
                    return JsonResponseBadRequest(err.detail)


def update_course_advanced_settings(course_block: CourseBlock, data: Dict, user: User) -> Dict:
    """
    Helper function to update course advanced settings from API data.

    This function takes JSON data returned from the API and applies changes from
    it to the course advanced settings.

    Args:
        course_block (CourseBlock): The course run object on which to operate.
        data (Dict): JSON data as found the ``request.data``
        user (User): The user performing the operation

    Returns:
        Dict: The updated data after applying changes based on supplied data.
    """
    try:
        # validate data formats and update the course block.
        # Note: don't update mongo yet, but wait until after any tabs are changed
        is_valid, errors, updated_data = CourseMetadata.validate_and_update_from_json(
            course_block,
            data,
            user=user,
        )

        if not is_valid:
            raise ValidationError(errors)

        try:
            # update the course tabs if required by any setting changes
            _refresh_course_tabs(user, course_block)
        except InvalidTabsException as err:
            log.exception(str(err))
            response_message = [
                {
                    'message': _('An error occurred while trying to save your tabs'),
                    'model': {'display_name': _('Tabs Exception')}
                }
            ]
            raise ValidationError(response_message) from err

        # now update mongo
        modulestore().update_item(course_block, user.id)

        return updated_data

    # Handle all errors that validation doesn't catch
    except (TypeError, ValueError, InvalidTabsException) as err:
        raise ValidationError(django.utils.html.escape(str(err))) from err


class TextbookValidationError(Exception):
    "An error thrown when a textbook input is invalid"
    pass  # lint-amnesty, pylint: disable=unnecessary-pass


def validate_textbooks_json(text):
    """
    Validate the given text as representing a single PDF textbook
    """
    if isinstance(text, (bytes, bytearray)):  # data appears as bytes
        text = text.decode('utf-8')
    try:
        textbooks = json.loads(text)
    except ValueError:
        raise TextbookValidationError("invalid JSON")  # lint-amnesty, pylint: disable=raise-missing-from
    if not isinstance(textbooks, (list, tuple)):
        raise TextbookValidationError("must be JSON list")
    for textbook in textbooks:
        validate_textbook_json(textbook)
    # check specified IDs for uniqueness
    all_ids = [textbook["id"] for textbook in textbooks if "id" in textbook]
    unique_ids = set(all_ids)
    if len(all_ids) > len(unique_ids):
        raise TextbookValidationError("IDs must be unique")
    return textbooks


def validate_textbook_json(textbook):
    """
    Validate the given text as representing a list of PDF textbooks
    """
    if isinstance(textbook, (bytes, bytearray)):  # data appears as bytes
        textbook = textbook.decode('utf-8')
    if isinstance(textbook, str):
        try:
            textbook = json.loads(textbook)
        except ValueError:
            raise TextbookValidationError("invalid JSON")  # lint-amnesty, pylint: disable=raise-missing-from
    if not isinstance(textbook, dict):
        raise TextbookValidationError("must be JSON object")
    if not textbook.get("tab_title"):
        raise TextbookValidationError("must have tab_title")
    tid = str(textbook.get("id", ""))
    if tid and not tid[0].isdigit():
        raise TextbookValidationError("textbook ID must start with a digit")
    return textbook


def assign_textbook_id(textbook, used_ids=()):
    """
    Return an ID that can be assigned to a textbook
    and doesn't match the used_ids
    """
    tid = BlockUsageLocator.clean(textbook["tab_title"])
    if not tid[0].isdigit():
        # stick a random digit in front
        tid = random.choice(string.digits) + tid
    while tid in used_ids:
        # add a random ASCII character to the end
        tid = tid + random.choice(string.ascii_lowercase)
    return tid


@require_http_methods(("GET", "POST", "PUT"))
@login_required
@ensure_csrf_cookie
def textbooks_list_handler(request, course_key_string):
    """
    A RESTful handler for textbook collections.

    GET
        html: return textbook list page (Backbone application)
        json: return JSON representation of all textbooks in this course
    POST
        json: create a new textbook for this course
    PUT
        json: overwrite all textbooks in the course with the given list
    """
    course_key = CourseKey.from_string(course_key_string)
    store = modulestore()
    with store.bulk_operations(course_key):
        course = get_course_and_check_access(course_key, request.user)

        if "application/json" not in request.META.get('HTTP_ACCEPT', 'text/html'):
            # return HTML page
            if use_new_textbooks_page(course_key):
                return redirect(get_textbooks_url(course_key))
            textbooks_context = get_textbooks_context(course)
            return render_to_response('textbooks.html', textbooks_context)

        # from here on down, we know the client has requested JSON
        if request.method == 'GET':
            return JsonResponse(course.pdf_textbooks)
        elif request.method == 'PUT':
            try:
                textbooks = validate_textbooks_json(request.body)
            except TextbookValidationError as err:
                return JsonResponse({"error": str(err)}, status=400)

            tids = {t["id"] for t in textbooks if "id" in t}
            for textbook in textbooks:
                if "id" not in textbook:
                    tid = assign_textbook_id(textbook, tids)
                    textbook["id"] = tid
                    tids.add(tid)

            if not any(tab['type'] == 'pdf_textbooks' for tab in course.tabs):
                course.tabs.append(CourseTab.load('pdf_textbooks'))
            course.pdf_textbooks = textbooks
            store.update_item(course, request.user.id)
            return JsonResponse(course.pdf_textbooks)
        elif request.method == 'POST':
            # create a new textbook for the course
            try:
                textbook = validate_textbook_json(request.body)
            except TextbookValidationError as err:
                return JsonResponse({"error": str(err)}, status=400)
            if not textbook.get("id"):
                tids = {t["id"] for t in course.pdf_textbooks if "id" in t}
                textbook["id"] = assign_textbook_id(textbook, tids)
            existing = course.pdf_textbooks
            existing.append(textbook)
            course.pdf_textbooks = existing
            if not any(tab['type'] == 'pdf_textbooks' for tab in course.tabs):
                course.tabs.append(CourseTab.load('pdf_textbooks'))
            store.update_item(course, request.user.id)
            resp = JsonResponse(textbook, status=201)
            resp["Location"] = reverse_course_url(
                'textbooks_detail_handler',
                course.id,
                kwargs={'textbook_id': textbook["id"]}
            )
            return resp


@login_required
@ensure_csrf_cookie
@require_http_methods(("GET", "POST", "PUT", "DELETE"))
def textbooks_detail_handler(request, course_key_string, textbook_id):
    """
    JSON API endpoint for manipulating a textbook via its internal ID.
    Used by the Backbone application.

    GET
        json: return JSON representation of textbook
    POST or PUT
        json: update textbook based on provided information
    DELETE
        json: remove textbook
    """
    course_key = CourseKey.from_string(course_key_string)
    store = modulestore()
    with store.bulk_operations(course_key):
        course_block = get_course_and_check_access(course_key, request.user)
        matching_id = [tb for tb in course_block.pdf_textbooks
                       if str(tb.get("id")) == str(textbook_id)]
        if matching_id:
            textbook = matching_id[0]
        else:
            textbook = None

        if request.method == 'GET':
            if not textbook:
                return JsonResponse(status=404)
            return JsonResponse(textbook)
        elif request.method in ('POST', 'PUT'):  # can be either and sometimes django is rewriting one to the other
            try:
                new_textbook = validate_textbook_json(request.body)
            except TextbookValidationError as err:
                return JsonResponse({"error": str(err)}, status=400)
            new_textbook["id"] = textbook_id
            if textbook:
                i = course_block.pdf_textbooks.index(textbook)
                new_textbooks = course_block.pdf_textbooks[0:i]
                new_textbooks.append(new_textbook)
                new_textbooks.extend(course_block.pdf_textbooks[i + 1:])
                course_block.pdf_textbooks = new_textbooks
            else:
                course_block.pdf_textbooks.append(new_textbook)
            store.update_item(course_block, request.user.id)
            return JsonResponse(new_textbook, status=201)
        elif request.method == 'DELETE':
            if not textbook:
                return JsonResponse(status=404)
            i = course_block.pdf_textbooks.index(textbook)
            remaining_textbooks = course_block.pdf_textbooks[0:i]
            remaining_textbooks.extend(course_block.pdf_textbooks[i + 1:])
            course_block.pdf_textbooks = remaining_textbooks
            store.update_item(course_block, request.user.id)
            return JsonResponse()


def remove_content_or_experiment_group(request, store, course, configuration, group_configuration_id, group_id=None):
    """
    Remove content group or experiment group configuration only if it's not in use.
    """
    configuration_index = course.user_partitions.index(configuration)
    if configuration.scheme.name == RANDOM_SCHEME:
        usages = GroupConfiguration.get_content_experiment_usage_info(store, course)
        used = int(group_configuration_id) in usages

        if used:
            return JsonResponse(
                {"error": _("This group configuration is in use and cannot be deleted.")},
                status=400
            )
        course.user_partitions.pop(configuration_index)
    elif configuration.scheme.name == COHORT_SCHEME:
        if not group_id:
            return JsonResponse(status=404)

        group_id = int(group_id)
        usages = GroupConfiguration.get_partitions_usage_info(store, course)
        used = group_id in usages[configuration.id]

        if used:
            return JsonResponse(
                {"error": _("This content group is in use and cannot be deleted.")},
                status=400
            )

        matching_groups = [group for group in configuration.groups if group.id == group_id]
        if matching_groups:
            group_index = configuration.groups.index(matching_groups[0])
            configuration.groups.pop(group_index)
        else:
            return JsonResponse(status=404)

        course.user_partitions[configuration_index] = configuration

    store.update_item(course, request.user.id)
    return JsonResponse(status=204)


@require_http_methods(("GET", "POST"))
@login_required
@ensure_csrf_cookie
def group_configurations_list_handler(request, course_key_string):
    """
    A RESTful handler for Group Configurations

    GET
        html: return Group Configurations list page (Backbone application)
    POST
        json: create new group configuration
    """
    course_key = CourseKey.from_string(course_key_string)
    store = modulestore()
    with store.bulk_operations(course_key):
        course = get_course_and_check_access(course_key, request.user)

        if 'text/html' in request.META.get('HTTP_ACCEPT', 'text/html'):
            if use_new_group_configurations_page(course_key):
                return redirect(get_group_configurations_url(course_key))
            group_configurations_context = get_group_configurations_context(course, store)
            return render_to_response('group_configurations.html', group_configurations_context)
        elif "application/json" in request.META.get('HTTP_ACCEPT'):
            if request.method == 'POST':
                # create a new group configuration for the course
                try:
                    new_configuration = GroupConfiguration(request.body, course).get_user_partition()
                except GroupConfigurationsValidationError as err:
                    return JsonResponse({"error": str(err)}, status=400)

                course.user_partitions.append(new_configuration)
                response = JsonResponse(new_configuration.to_json(), status=201)

                response["Location"] = reverse_course_url(
                    'group_configurations_detail_handler',
                    course.id,
                    kwargs={'group_configuration_id': new_configuration.id}
                )
                store.update_item(course, request.user.id)
                return response
        else:
            return HttpResponse(status=406)


@login_required
@ensure_csrf_cookie
@require_http_methods(("POST", "PUT", "DELETE"))
def group_configurations_detail_handler(request, course_key_string, group_configuration_id, group_id=None):
    """
    JSON API endpoint for manipulating a group configuration via its internal ID.
    Used by the Backbone application.

    POST or PUT
        json: update group configuration based on provided information
    """
    course_key = CourseKey.from_string(course_key_string)
    store = modulestore()
    with store.bulk_operations(course_key):
        course = get_course_and_check_access(course_key, request.user)
        matching_id = [p for p in course.user_partitions
                       if str(p.id) == str(group_configuration_id)]
        if matching_id:
            configuration = matching_id[0]
        else:
            configuration = None

        if request.method in ('POST', 'PUT'):  # can be either and sometimes django is rewriting one to the other
            try:
                new_configuration = GroupConfiguration(request.body, course, group_configuration_id).get_user_partition()  # lint-amnesty, pylint: disable=line-too-long
            except GroupConfigurationsValidationError as err:
                return JsonResponse({"error": str(err)}, status=400)

            if configuration:
                index = course.user_partitions.index(configuration)
                course.user_partitions[index] = new_configuration
            else:
                course.user_partitions.append(new_configuration)
            store.update_item(course, request.user.id)
            configuration = GroupConfiguration.update_usage_info(store, course, new_configuration)
            return JsonResponse(configuration, status=201)

        elif request.method == "DELETE":
            if not configuration:
                return JsonResponse(status=404)

            return remove_content_or_experiment_group(
                request=request,
                store=store,
                course=course,
                configuration=configuration,
                group_configuration_id=group_configuration_id,
                group_id=group_id
            )


def are_content_experiments_enabled(course):
    """
    Returns True if content experiments have been enabled for the course.
    """
    return (
        'split_test' in ADVANCED_COMPONENT_TYPES and
        'split_test' in course.advanced_modules
    )


def _get_course_creator_status(user):
    """
    Helper method for returning the course creator status for a particular user,
    taking into account the values of DISABLE_COURSE_CREATION and ENABLE_CREATOR_GROUP.

    If the user passed in has not previously visited the index page, it will be
    added with status 'unrequested' if the course creator group is in use.
    """

    if user.is_staff:
        course_creator_status = 'granted'
    elif settings.FEATURES.get('DISABLE_COURSE_CREATION', False):
        course_creator_status = 'disallowed_for_this_site'
    elif settings.FEATURES.get('ENABLE_CREATOR_GROUP', False):
        course_creator_status = get_course_creator_status(user)
        if course_creator_status is None:
            # User not grandfathered in as an existing user, has not previously visited the dashboard page.
            # Add the user to the course creator admin table with status 'unrequested'.
            add_user_with_status_unrequested(user)
            course_creator_status = get_course_creator_status(user)
    else:
        course_creator_status = 'granted'

    return course_creator_status


def get_allowed_organizations(user):
    """
    Helper method for returning the list of organizations for which the user is allowed to create courses.
    """
    if settings.FEATURES.get('ENABLE_CREATOR_GROUP', False):
        return get_organizations(user)
    else:
        return []


def get_allowed_organizations_for_libraries(user):
    """
    Helper method for returning the list of organizations for which the user is allowed to create libraries.
    """
    if settings.FEATURES.get('ENABLE_ORGANIZATION_STAFF_ACCESS_FOR_CONTENT_LIBRARIES', False):
        return get_organizations_for_non_course_creators(user)
    elif settings.FEATURES.get('ENABLE_CREATOR_GROUP', False):
        return get_organizations(user)
    else:
        return []


def user_can_create_organizations(user):
    """
    Returns True if the user can create organizations.
    """
    return user.is_staff or not settings.FEATURES.get('ENABLE_CREATOR_GROUP', False)


def get_organizations_for_non_course_creators(user):
    """
    Returns the list of organizations which the user is a staff member of, as a list of strings.
    """
    orgs_map = set()
    orgs = OrgStaffRole().get_orgs_for_user(user)
    # deduplicate
    for org in orgs:
        orgs_map.add(org)
    return list(orgs_map)


def get_organizations(user):
    """
    Returns the list of organizations for which the user is allowed to create courses.
    """
    course_creator = CourseCreator.objects.filter(user=user).first()
    if not course_creator or course_creator.state != CourseCreator.GRANTED:
        return []
    elif course_creator.all_organizations:
        organizations = Organization.objects.all().values_list('short_name', flat=True)
    else:
        organizations = course_creator.organizations.all().values_list('short_name', flat=True)

    return organizations
