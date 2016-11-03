"""
Views related to operations on course objects
"""
import copy
import json
import logging
import random
import string  # pylint: disable=deprecated-module

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound, Http404
from django.shortcuts import redirect
import django.utils
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_http_methods, require_GET
from django.views.decorators.csrf import ensure_csrf_cookie

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import Location

from .component import (
    ADVANCED_COMPONENT_TYPES,
)
from .item import create_xblock_info
from .library import LIBRARIES_ENABLED
from ccx_keys.locator import CCXLocator
from contentstore.course_group_config import (
    COHORT_SCHEME,
    GroupConfiguration,
    GroupConfigurationsValidationError,
    RANDOM_SCHEME,
)
from contentstore.course_info_model import get_course_updates, update_course_updates, delete_course_update
from contentstore.courseware_index import CoursewareSearchIndexer, SearchIndexingError
from contentstore.push_notification import push_notification_enabled
from contentstore.tasks import rerun_course
from contentstore.utils import (
    add_instructor,
    initialize_permissions,
    get_lms_link_for_item,
    remove_all_instructors,
    reverse_course_url,
    reverse_library_url,
    reverse_usage_url,
    reverse_url,
)
from contentstore.views.entrance_exam import (
    create_entrance_exam,
    delete_entrance_exam,
    update_entrance_exam,
)
from course_action_state.managers import CourseActionStateItemNotFoundError
from course_action_state.models import CourseRerunState, CourseRerunUIStateManager
from course_creators.views import get_course_creator_status, add_user_with_status_unrequested
from edxmako.shortcuts import render_to_response
from models.settings.course_grading import CourseGradingModel
from models.settings.course_metadata import CourseMetadata
from models.settings.encoder import CourseSettingsEncoder
from openedx.core.djangoapps.content.course_structures.api.v0 import api, errors
from openedx.core.djangoapps.credit.api import is_credit_course, get_credit_requirements
from openedx.core.djangoapps.credit.tasks import update_credit_course_requirements
from openedx.core.djangoapps.models.course_details import CourseDetails
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.programs.utils import get_programs
from openedx.core.djangoapps.self_paced.models import SelfPacedConfiguration
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.lib.course_tabs import CourseTabPluginManager
from openedx.core.lib.courses import course_image_url
from openedx.core.djangolib.js_utils import dump_js_escaped_json
from student import auth
from student.auth import has_course_author_access, has_studio_write_access, has_studio_read_access
from student.roles import (
    CourseInstructorRole, CourseStaffRole, CourseCreatorRole, GlobalStaff, UserBasedRole
)
from util.course import get_lms_link_for_about_page
from util.date_utils import get_default_time_display
from util.json_request import JsonResponse, JsonResponseBadRequest, expect_json
from util.milestones_helpers import (
    is_entrance_exams_enabled,
    is_prerequisite_courses_enabled,
    is_valid_course_key,
    set_prerequisite_courses,
)
from util.organizations_helpers import (
    add_organization_course,
    get_organization_by_short_name,
    organizations_enabled,
)
from util.string_utils import _has_non_ascii_characters
from xblock_django.api import deprecated_xblocks
from xmodule.contentstore.content import StaticContent
from xmodule.course_module import CourseFields
from xmodule.course_module import DEFAULT_START_DATE
from xmodule.error_module import ErrorDescriptor
from xmodule.modulestore import EdxJSONEncoder
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError, DuplicateCourseError
from xmodule.tabs import CourseTab, CourseTabList, InvalidTabsException


log = logging.getLogger(__name__)

__all__ = ['course_info_handler', 'course_handler', 'course_listing',
           'course_info_update_handler', 'course_search_index_handler',
           'course_rerun_handler',
           'settings_handler',
           'grading_handler',
           'advanced_settings_handler',
           'course_notifications_handler',
           'textbooks_list_handler', 'textbooks_detail_handler',
           'group_configurations_list_handler', 'group_configurations_detail_handler']


class AccessListFallback(Exception):
    """
    An exception that is raised whenever we need to `fall back` to fetching *all* courses
    available to a user, rather than using a shorter method (i.e. fetching by group)
    """
    pass


def get_course_and_check_access(course_key, user, depth=0):
    """
    Internal method used to calculate and return the locator and course module
    for the view functions in this file.
    """
    if not has_studio_read_access(user, course_key):
        raise PermissionDenied()
    course_module = modulestore().get_course(course_key, depth=depth)
    return course_module


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


def _dismiss_notification(request, course_action_state_id):  # pylint: disable=unused-argument
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


# pylint: disable=unused-argument
@login_required
def course_handler(request, course_key_string=None):
    """
    The restful handler for course specific requests.
    It provides the course tree with the necessary information for identifying and labeling the parts. The root
    will typically be a 'course' object but may not be especially as we support modules.

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
        response_format = request.GET.get('format') or request.POST.get('format') or 'html'
        if response_format == 'json' or 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json'):
            if request.method == 'GET':
                course_key = CourseKey.from_string(course_key_string)
                with modulestore().bulk_operations(course_key):
                    course_module = get_course_and_check_access(course_key, request.user, depth=None)
                    return JsonResponse(_course_outline_json(request, course_module))
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
                return redirect(reverse("home"))
            else:
                return course_index(request, CourseKey.from_string(course_key_string))
        else:
            return HttpResponseNotFound()
    except InvalidKeyError:
        raise Http404


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
        course_module = get_course_and_check_access(course_key, request.user, depth=3)
        if request.method == 'GET':
            return render_to_response('course-create-rerun.html', {
                'source_course_key': course_key,
                'display_name': course_module.display_name,
                'user': request.user,
                'course_creator_status': _get_course_creator_status(request.user),
                'allow_unicode_course_id': settings.FEATURES.get('ALLOW_UNICODE_COURSE_ID', False)
            })


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


def _course_outline_json(request, course_module):
    """
    Returns a JSON representation of the course module and recursively all of its children.
    """
    return create_xblock_info(
        course_module,
        include_child_info=True,
        course_outline=True,
        include_children_predicate=lambda xblock: not xblock.category == 'vertical',
        user=request.user
    )


def get_in_process_course_actions(request):
    """
     Get all in-process course actions
    """
    return [
        course for course in
        CourseRerunState.objects.find_all(
            exclude_args={'state': CourseRerunUIStateManager.State.SUCCEEDED}, should_display=True
        )
        if has_studio_read_access(request.user, course.course_key)
    ]


def _accessible_courses_summary_list(request):
    """
    List all courses available to the logged in user by iterating through all the courses
    """
    def course_filter(course_summary):
        """
        Filter out unusable and inaccessible courses
        """
        # pylint: disable=fixme
        # TODO remove this condition when templates purged from db
        if course_summary.location.course == 'templates':
            return False

        return has_studio_read_access(request.user, course_summary.id)

    courses_summary = filter(course_filter, modulestore().get_course_summaries())
    in_process_course_actions = get_in_process_course_actions(request)
    return courses_summary, in_process_course_actions


def _accessible_courses_list(request):
    """
    List all courses available to the logged in user by iterating through all the courses
    """
    def course_filter(course):
        """
        Filter out unusable and inaccessible courses
        """
        if isinstance(course, ErrorDescriptor):
            return False

        # Custom Courses for edX (CCX) is an edX feature for re-using course content.
        # CCXs cannot be edited in Studio (aka cms) and should not be shown in this dashboard.
        if isinstance(course.id, CCXLocator):
            return False

        # pylint: disable=fixme
        # TODO remove this condition when templates purged from db
        if course.location.course == 'templates':
            return False

        return has_studio_read_access(request.user, course.id)

    courses = filter(course_filter, modulestore().get_courses())

    in_process_course_actions = get_in_process_course_actions(request)
    return courses, in_process_course_actions


def _accessible_courses_list_from_groups(request):
    """
    List all courses available to the logged in user by reversing access group names
    """
    def filter_ccx(course_access):
        """ CCXs cannot be edited in Studio and should not be shown in this dashboard """
        return not isinstance(course_access.course_id, CCXLocator)

    courses_list = {}
    in_process_course_actions = []

    instructor_courses = UserBasedRole(request.user, CourseInstructorRole.ROLE).courses_with_role()
    staff_courses = UserBasedRole(request.user, CourseStaffRole.ROLE).courses_with_role()
    all_courses = filter(filter_ccx, instructor_courses | staff_courses)

    for course_access in all_courses:
        course_key = course_access.course_id
        if course_key is None:
            # If the course_access does not have a course_id, it's an org-based role, so we fall back
            raise AccessListFallback
        if course_key not in courses_list:
            # check for any course action state for this course
            in_process_course_actions.extend(
                CourseRerunState.objects.find_all(
                    exclude_args={'state': CourseRerunUIStateManager.State.SUCCEEDED},
                    should_display=True,
                    course_key=course_key,
                )
            )
            # check for the course itself
            try:
                course = modulestore().get_course(course_key)
            except ItemNotFoundError:
                # If a user has access to a course that doesn't exist, don't do anything with that course
                pass

            if course is not None and not isinstance(course, ErrorDescriptor):
                # ignore deleted, errored or ccx courses
                courses_list[course_key] = course

    return courses_list.values(), in_process_course_actions


def _accessible_libraries_list(user):
    """
    List all libraries available to the logged in user by iterating through all libraries
    """
    # No need to worry about ErrorDescriptors - split's get_libraries() never returns them.
    return [lib for lib in modulestore().get_libraries() if has_studio_read_access(user, lib.location.library_key)]


@login_required
@ensure_csrf_cookie
def course_listing(request):
    """
    List all courses available to the logged in user
    """
    courses, in_process_course_actions = get_courses_accessible_to_user(request)
    user = request.user
    user_has_permission =\
        user.is_active and (user.is_staff or CourseCreatorRole().has_user(user))
    libraries = _accessible_libraries_list(request.user) if LIBRARIES_ENABLED and user_has_permission else []

    programs_config = ProgramsApiConfig.current()
    raw_programs = get_programs(request.user) if programs_config.is_studio_tab_enabled else []

    # Sort programs alphabetically by name.
    # TODO: Support ordering in the Programs API itself.
    programs = sorted(raw_programs, key=lambda p: p['name'].lower())

    def format_in_process_course_view(uca):
        """
        Return a dict of the data which the view requires for each unsucceeded course
        """
        return {
            'display_name': uca.display_name,
            'course_key': unicode(uca.course_key),
            'org': uca.course_key.org,
            'number': uca.course_key.course,
            'run': uca.course_key.run,
            'is_failed': True if uca.state == CourseRerunUIStateManager.State.FAILED else False,
            'is_in_progress': True if uca.state == CourseRerunUIStateManager.State.IN_PROGRESS else False,
            'dismiss_link': reverse_course_url(
                'course_notifications_handler',
                uca.course_key,
                kwargs={
                    'action_state_id': uca.id,
                },
            ) if uca.state == CourseRerunUIStateManager.State.FAILED else ''
        }

    def format_library_for_view(library):
        """
        Return a dict of the data which the view requires for each library
        """
        return {
            'display_name': library.display_name,
            'library_key': unicode(library.location.library_key),
            'url': reverse_library_url('library_handler', unicode(library.location.library_key)),
            'org': library.display_org_with_default,
            'number': library.display_number_with_default,
            'can_edit': has_studio_write_access(request.user, library.location.library_key),
        }

    courses = _remove_in_process_courses(courses, in_process_course_actions)
    in_process_course_actions = [format_in_process_course_view(uca) for uca in in_process_course_actions]

    return render_to_response('index.html', {
        'courses': courses,
        'in_process_course_actions': in_process_course_actions,
        'user': request.user,
        'request_course_creator_url': reverse('contentstore.views.request_course_creator'),
        'course_creator_status': _get_course_creator_status(request.user),
        'rerun_creator_status': GlobalStaff().has_user(request.user),
        'allow_unicode_course_id': settings.FEATURES.get('ALLOW_UNICODE_COURSE_ID', False),
        'allow_course_reruns': settings.FEATURES.get('ALLOW_COURSE_RERUNS', True),
        'libraries_enabled': LIBRARIES_ENABLED,
        'libraries': [format_library_for_view(lib) for lib in libraries],
        'library_creator_status': _get_library_creator_status(user),
        'is_programs_enabled': programs_config.is_studio_tab_enabled and request.user.is_staff,
        'programs': programs,
        'program_authoring_url': reverse('programs')
    })


def _get_rerun_link_for_item(course_key):
    """ Returns the rerun link for the given course key. """
    return reverse_course_url('course_rerun_handler', course_key)


def _deprecated_blocks_info(course_module, deprecated_block_types):
    """
    Returns deprecation information about `deprecated_block_types`

    Arguments:
        course_module (CourseDescriptor): course object
        deprecated_block_types (list): list of deprecated blocks types

    Returns:
        Dict with following keys:
        block_types (list): list containing types of all deprecated blocks
        block_types_enabled (bool): True if any or all `deprecated_blocks` present in Advanced Module List else False
        blocks (list): List of `deprecated_block_types` component names and their parent's url
        advance_settings_url (str): URL to advance settings page
    """
    data = {
        'block_types': deprecated_block_types,
        'block_types_enabled': any(
            block_type in course_module.advanced_modules for block_type in deprecated_block_types
        ),
        'blocks': [],
        'advance_settings_url': reverse_course_url('advanced_settings_handler', course_module.id)
    }

    try:
        structure_data = api.course_structure(course_module.id, block_types=deprecated_block_types)
    except errors.CourseStructureNotAvailableError:
        return data

    for block in structure_data['blocks'].values():
        data['blocks'].append([reverse_usage_url('container_handler', block['parent']), block['display_name']])

    return data


@login_required
@ensure_csrf_cookie
def course_index(request, course_key):
    """
    Display an editable course overview.

    org, course, name: Attributes of the Location for the item to edit
    """
    # A depth of None implies the whole course. The course outline needs this in order to compute has_changes.
    # A unit may not have a draft version, but one of its components could, and hence the unit itself has changes.
    with modulestore().bulk_operations(course_key):
        course_module = get_course_and_check_access(course_key, request.user, depth=None)
        if not course_module:
            raise Http404
        lms_link = get_lms_link_for_item(course_module.location)
        reindex_link = None
        if settings.FEATURES.get('ENABLE_COURSEWARE_INDEX', False):
            reindex_link = "/course/{course_id}/search_reindex".format(course_id=unicode(course_key))
        sections = course_module.get_children()
        course_structure = _course_outline_json(request, course_module)
        locator_to_show = request.GET.get('show', None)
        course_release_date = get_default_time_display(course_module.start) if course_module.start != DEFAULT_START_DATE else _("Unscheduled")
        settings_url = reverse_course_url('settings_handler', course_key)

        try:
            current_action = CourseRerunState.objects.find_first(course_key=course_key, should_display=True)
        except (ItemNotFoundError, CourseActionStateItemNotFoundError):
            current_action = None

        deprecated_block_names = [block.name for block in deprecated_xblocks()]
        deprecated_blocks_info = _deprecated_blocks_info(course_module, deprecated_block_names)

        return render_to_response('course_outline.html', {
            'context_course': course_module,
            'lms_link': lms_link,
            'sections': sections,
            'course_structure': course_structure,
            'initial_state': course_outline_initial_state(locator_to_show, course_structure) if locator_to_show else None,
            'rerun_notification_id': current_action.id if current_action else None,
            'course_release_date': course_release_date,
            'settings_url': settings_url,
            'reindex_link': reindex_link,
            'deprecated_blocks_info': deprecated_blocks_info,
            'notification_dismiss_url': reverse_course_url(
                'course_notifications_handler',
                current_action.course_key,
                kwargs={
                    'action_state_id': current_action.id,
                },
            ) if current_action else None,
        })


def get_courses_accessible_to_user(request):
    """
    Try to get all courses by first reversing django groups and fallback to old method if it fails
    Note: overhead of pymongo reads will increase if getting courses from django groups fails
    """
    if GlobalStaff().has_user(request.user):
        # user has global access so no need to get courses from django groups
        courses, in_process_course_actions = _accessible_courses_summary_list(request)
    else:
        try:
            courses, in_process_course_actions = _accessible_courses_list_from_groups(request)
        except AccessListFallback:
            # user have some old groups or there was some error getting courses from django groups
            # so fallback to iterating through all courses
            courses, in_process_course_actions = _accessible_courses_summary_list(request)
    return courses, in_process_course_actions


def _remove_in_process_courses(courses, in_process_course_actions):
    """
    removes any in-process courses in courses list. in-process actually refers to courses
    that are in the process of being generated for re-run
    """
    def format_course_for_view(course):
        """
        Return a dict of the data which the view requires for each course
        """
        return {
            'display_name': course.display_name,
            'course_key': unicode(course.location.course_key),
            'url': reverse_course_url('course_handler', course.id),
            'lms_link': get_lms_link_for_item(course.location),
            'rerun_link': _get_rerun_link_for_item(course.id),
            'org': course.display_org_with_default,
            'number': course.display_number_with_default,
            'run': course.location.run
        }

    in_process_action_course_keys = [uca.course_key for uca in in_process_course_actions]
    courses = [
        format_course_for_view(course)
        for course in courses
        if not isinstance(course, ErrorDescriptor) and (course.id not in in_process_action_course_keys)
    ]
    return courses


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
    if not auth.user_has_role(request.user, CourseCreatorRole()):
        raise PermissionDenied()

    try:
        org = request.json.get('org')
        course = request.json.get('number', request.json.get('course'))
        display_name = request.json.get('display_name')
        # force the start date for reruns and allow us to override start via the client
        start = request.json.get('start', CourseFields.start.default)
        run = request.json.get('run')

        # allow/disable unicode characters in course_id according to settings
        if not settings.FEATURES.get('ALLOW_UNICODE_COURSE_ID'):
            if _has_non_ascii_characters(org) or _has_non_ascii_characters(course) or _has_non_ascii_characters(run):
                return JsonResponse(
                    {'error': _('Special characters not allowed in organization, course number, and course run.')},
                    status=400
                )

        fields = {'start': start}
        if display_name is not None:
            fields['display_name'] = display_name

        # Set a unique wiki_slug for newly created courses. To maintain active wiki_slugs for
        # existing xml courses this cannot be changed in CourseDescriptor.
        # # TODO get rid of defining wiki slug in this org/course/run specific way and reconcile
        # w/ xmodule.course_module.CourseDescriptor.__init__
        wiki_slug = u"{0}.{1}.{2}".format(org, course, run)
        definition_data = {'wiki_slug': wiki_slug}
        fields.update(definition_data)

        if 'source_course_key' in request.json:
            return _rerun_course(request, org, course, run, fields)
        else:
            return _create_new_course(request, org, course, run, fields)

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
            "ErrMsg": _("Unable to create course '{name}'.\n\n{err}").format(name=display_name, err=error.message)}
        )


def _create_new_course(request, org, number, run, fields):
    """
    Create a new course.
    Returns the URL for the course overview page.
    Raises DuplicateCourseError if the course already exists
    """
    org_data = get_organization_by_short_name(org)
    if not org_data and organizations_enabled():
        return JsonResponse(
            {'error': _('You must link this course to an organization in order to continue. '
                        'Organization you selected does not exist in the system, '
                        'you will need to add it to the system')},
            status=400
        )
    store_for_new_course = modulestore().default_modulestore.get_modulestore_type()
    new_course = create_new_course_in_store(store_for_new_course, request.user, org, number, run, fields)
    add_organization_course(org_data, new_course.id)
    return JsonResponse({
        'url': reverse_course_url('course_handler', new_course.id),
        'course_key': unicode(new_course.id),
    })


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


def _rerun_course(request, org, number, run, fields):
    """
    Reruns an existing course.
    Returns the URL for the course listing page.
    """
    source_course_key = CourseKey.from_string(request.json.get('source_course_key'))

    # verify user has access to the original course
    if not has_studio_write_access(request.user, source_course_key):
        raise PermissionDenied()

    # create destination course key
    store = modulestore()
    with store.default_store('split'):
        destination_course_key = store.make_course_key(org, number, run)

    # verify org course and run don't already exist
    if store.has_course(destination_course_key, ignore_case=True):
        raise DuplicateCourseError(source_course_key, destination_course_key)

    # Make sure user has instructor and staff access to the destination course
    # so the user can see the updated status for that course
    add_instructor(destination_course_key, request.user, request.user)

    # Mark the action as initiated
    CourseRerunState.objects.initiated(source_course_key, destination_course_key, request.user, fields['display_name'])

    # Clear the fields that must be reset for the rerun
    fields['advertised_start'] = None

    # Rerun the course as a new celery task
    json_fields = json.dumps(fields, cls=EdxJSONEncoder)
    rerun_course.delay(unicode(source_course_key), unicode(destination_course_key), request.user.id, json_fields)

    # Return course listing page
    return JsonResponse({
        'url': reverse_url('course_handler'),
        'destination_course_key': unicode(destination_course_key)
    })


# pylint: disable=unused-argument
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
        raise Http404

    with modulestore().bulk_operations(course_key):
        course_module = get_course_and_check_access(course_key, request.user)
        if not course_module:
            raise Http404
        if 'text/html' in request.META.get('HTTP_ACCEPT', 'text/html'):
            return render_to_response(
                'course_info.html',
                {
                    'context_course': course_module,
                    'updates_url': reverse_course_url('course_info_update_handler', course_key),
                    'handouts_locator': course_key.make_usage_key('course_info', 'handouts'),
                    'base_asset_url': StaticContent.get_base_url_path_for_course_assets(course_module.id),
                    'push_notification_enabled': push_notification_enabled()
                }
            )
        else:
            return HttpResponseBadRequest("Only supports html requests")


# pylint: disable=unused-argument
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
        except:
            return HttpResponseBadRequest(
                "Failed to delete",
                content_type="text/plain"
            )
    # can be either and sometimes django is rewriting one to the other:
    elif request.method in ('POST', 'PUT'):
        try:
            return JsonResponse(update_course_updates(usage_key, request.json, provided_id, request.user))
        except:
            return HttpResponseBadRequest(
                "Failed to save",
                content_type="text/plain"
            )


@login_required
@ensure_csrf_cookie
@require_http_methods(("GET", "PUT", "POST"))
@expect_json
def settings_handler(request, course_key_string):
    """
    Course settings for dates and about pages
    GET
        html: get the page
        json: get the CourseDetails model
    PUT
        json: update the Course and About xblocks through the CourseDetails model
    """
    course_key = CourseKey.from_string(course_key_string)
    credit_eligibility_enabled = settings.FEATURES.get('ENABLE_CREDIT_ELIGIBILITY', False)
    with modulestore().bulk_operations(course_key):
        course_module = get_course_and_check_access(course_key, request.user)
        if 'text/html' in request.META.get('HTTP_ACCEPT', '') and request.method == 'GET':
            upload_asset_url = reverse_course_url('assets_handler', course_key)

            # see if the ORG of this course can be attributed to a defined configuration . In that case, the
            # course about page should be editable in Studio
            marketing_site_enabled = configuration_helpers.get_value_for_org(
                course_module.location.org,
                'ENABLE_MKTG_SITE',
                settings.FEATURES.get('ENABLE_MKTG_SITE', False)
            )
            enable_extended_course_details = configuration_helpers.get_value_for_org(
                course_module.location.org,
                'ENABLE_EXTENDED_COURSE_DETAILS',
                settings.FEATURES.get('ENABLE_EXTENDED_COURSE_DETAILS', False)
            )

            about_page_editable = not marketing_site_enabled
            enrollment_end_editable = GlobalStaff().has_user(request.user) or not marketing_site_enabled
            short_description_editable = configuration_helpers.get_value_for_org(
                course_module.location.org,
                'EDITABLE_SHORT_DESCRIPTION',
                settings.FEATURES.get('EDITABLE_SHORT_DESCRIPTION', True)
            )
            self_paced_enabled = SelfPacedConfiguration.current().enabled

            settings_context = {
                'context_course': course_module,
                'course_locator': course_key,
                'lms_link_for_about_page': get_lms_link_for_about_page(course_key),
                'course_image_url': course_image_url(course_module, 'course_image'),
                'banner_image_url': course_image_url(course_module, 'banner_image'),
                'video_thumbnail_image_url': course_image_url(course_module, 'video_thumbnail_image'),
                'details_url': reverse_course_url('settings_handler', course_key),
                'about_page_editable': about_page_editable,
                'short_description_editable': short_description_editable,
                'upload_asset_url': upload_asset_url,
                'course_handler_url': reverse_course_url('course_handler', course_key),
                'language_options': settings.ALL_LANGUAGES,
                'credit_eligibility_enabled': credit_eligibility_enabled,
                'is_credit_course': False,
                'show_min_grade_warning': False,
                'enrollment_end_editable': enrollment_end_editable,
                'is_prerequisite_courses_enabled': is_prerequisite_courses_enabled(),
                'is_entrance_exams_enabled': is_entrance_exams_enabled(),
                'self_paced_enabled': self_paced_enabled,
                'enable_extended_course_details': enable_extended_course_details
            }
            if is_prerequisite_courses_enabled():
                courses, in_process_course_actions = get_courses_accessible_to_user(request)
                # exclude current course from the list of available courses
                courses = [course for course in courses if course.id != course_key]
                if courses:
                    courses = _remove_in_process_courses(courses, in_process_course_actions)
                settings_context.update({'possible_pre_requisite_courses': courses})

            if credit_eligibility_enabled:
                if is_credit_course(course_key):
                    # get and all credit eligibility requirements
                    credit_requirements = get_credit_requirements(course_key)
                    # pair together requirements with same 'namespace' values
                    paired_requirements = {}
                    for requirement in credit_requirements:
                        namespace = requirement.pop("namespace")
                        paired_requirements.setdefault(namespace, []).append(requirement)

                    # if 'minimum_grade_credit' of a course is not set or 0 then
                    # show warning message to course author.
                    show_min_grade_warning = False if course_module.minimum_grade_credit > 0 else True
                    settings_context.update(
                        {
                            'is_credit_course': True,
                            'credit_requirements': paired_requirements,
                            'show_min_grade_warning': show_min_grade_warning,
                        }
                    )

            return render_to_response('settings.html', settings_context)
        elif 'application/json' in request.META.get('HTTP_ACCEPT', ''):
            if request.method == 'GET':
                course_details = CourseDetails.fetch(course_key)
                return JsonResponse(
                    course_details,
                    # encoder serializes dates, old locations, and instances
                    encoder=CourseSettingsEncoder
                )
            # For every other possible method type submitted by the caller...
            else:
                # if pre-requisite course feature is enabled set pre-requisite course
                if is_prerequisite_courses_enabled():
                    prerequisite_course_keys = request.json.get('pre_requisite_courses', [])
                    if prerequisite_course_keys:
                        if not all(is_valid_course_key(course_key) for course_key in prerequisite_course_keys):
                            return JsonResponseBadRequest({"error": _("Invalid prerequisite course key")})
                        set_prerequisite_courses(course_key, prerequisite_course_keys)

                # If the entrance exams feature has been enabled, we'll need to check for some
                # feature-specific settings and handle them accordingly
                # We have to be careful that we're only executing the following logic if we actually
                # need to create or delete an entrance exam from the specified course
                if is_entrance_exams_enabled():
                    course_entrance_exam_present = course_module.entrance_exam_enabled
                    entrance_exam_enabled = request.json.get('entrance_exam_enabled', '') == 'true'
                    ee_min_score_pct = request.json.get('entrance_exam_minimum_score_pct', None)
                    # If the entrance exam box on the settings screen has been checked...
                    if entrance_exam_enabled:
                        # Load the default minimum score threshold from settings, then try to override it
                        entrance_exam_minimum_score_pct = float(settings.ENTRANCE_EXAM_MIN_SCORE_PCT)
                        if ee_min_score_pct:
                            entrance_exam_minimum_score_pct = float(ee_min_score_pct)
                        if entrance_exam_minimum_score_pct.is_integer():
                            entrance_exam_minimum_score_pct = entrance_exam_minimum_score_pct / 100
                        entrance_exam_minimum_score_pct = unicode(entrance_exam_minimum_score_pct)
                        # If there's already an entrance exam defined, we'll update the existing one
                        if course_entrance_exam_present:
                            exam_data = {
                                'entrance_exam_minimum_score_pct': entrance_exam_minimum_score_pct
                            }
                            update_entrance_exam(request, course_key, exam_data)
                        # If there's no entrance exam defined, we'll create a new one
                        else:
                            create_entrance_exam(request, course_key, entrance_exam_minimum_score_pct)

                    # If the entrance exam box on the settings screen has been unchecked,
                    # and the course has an entrance exam attached...
                    elif not entrance_exam_enabled and course_entrance_exam_present:
                        delete_entrance_exam(request, course_key)

                # Perform the normal update workflow for the CourseDetails model
                return JsonResponse(
                    CourseDetails.update_from_json(course_key, request.json, request.user),
                    encoder=CourseSettingsEncoder
                )


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
        course_module = get_course_and_check_access(course_key, request.user)

        if 'text/html' in request.META.get('HTTP_ACCEPT', '') and request.method == 'GET':
            course_details = CourseGradingModel.fetch(course_key)

            return render_to_response('settings_graders.html', {
                'context_course': course_module,
                'course_locator': course_key,
                'course_details': course_details,
                'grading_url': reverse_course_url('grading_handler', course_key),
                'is_credit_course': is_credit_course(course_key),
            })
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
                    update_credit_course_requirements.delay(unicode(course_key))

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


def _refresh_course_tabs(request, course_module):
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

    course_tabs = copy.copy(course_module.tabs)

    # Additionally update any tabs that are provided by non-dynamic course views
    for tab_type in CourseTabPluginManager.get_tab_types():
        if not tab_type.is_dynamic and tab_type.is_default:
            tab_enabled = tab_type.is_enabled(course_module, user=request.user)
            update_tab(course_tabs, tab_type, tab_enabled)

    CourseTabList.validate_tabs(course_tabs)

    # Save the tabs into the course if they have been changed
    if course_tabs != course_module.tabs:
        course_module.tabs = course_tabs


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
    course_key = CourseKey.from_string(course_key_string)
    with modulestore().bulk_operations(course_key):
        course_module = get_course_and_check_access(course_key, request.user)
        if 'text/html' in request.META.get('HTTP_ACCEPT', '') and request.method == 'GET':

            return render_to_response('settings_advanced.html', {
                'context_course': course_module,
                'advanced_dict': CourseMetadata.fetch(course_module),
                'advanced_settings_url': reverse_course_url('advanced_settings_handler', course_key)
            })
        elif 'application/json' in request.META.get('HTTP_ACCEPT', ''):
            if request.method == 'GET':
                return JsonResponse(CourseMetadata.fetch(course_module))
            else:
                try:
                    # validate data formats and update the course module.
                    # Note: don't update mongo yet, but wait until after any tabs are changed
                    is_valid, errors, updated_data = CourseMetadata.validate_and_update_from_json(
                        course_module,
                        request.json,
                        user=request.user,
                    )

                    if is_valid:
                        try:
                            # update the course tabs if required by any setting changes
                            _refresh_course_tabs(request, course_module)
                        except InvalidTabsException as err:
                            log.exception(err.message)
                            response_message = [
                                {
                                    'message': _('An error occurred while trying to save your tabs'),
                                    'model': {'display_name': _('Tabs Exception')}
                                }
                            ]
                            return JsonResponseBadRequest(response_message)

                        # now update mongo
                        modulestore().update_item(course_module, request.user.id)

                        return JsonResponse(updated_data)
                    else:
                        return JsonResponseBadRequest(errors)

                # Handle all errors that validation doesn't catch
                except (TypeError, ValueError, InvalidTabsException) as err:
                    return HttpResponseBadRequest(
                        django.utils.html.escape(err.message),
                        content_type="text/plain"
                    )


class TextbookValidationError(Exception):
    "An error thrown when a textbook input is invalid"
    pass


def validate_textbooks_json(text):
    """
    Validate the given text as representing a single PDF textbook
    """
    try:
        textbooks = json.loads(text)
    except ValueError:
        raise TextbookValidationError("invalid JSON")
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
    if isinstance(textbook, basestring):
        try:
            textbook = json.loads(textbook)
        except ValueError:
            raise TextbookValidationError("invalid JSON")
    if not isinstance(textbook, dict):
        raise TextbookValidationError("must be JSON object")
    if not textbook.get("tab_title"):
        raise TextbookValidationError("must have tab_title")
    tid = unicode(textbook.get("id", ""))
    if tid and not tid[0].isdigit():
        raise TextbookValidationError("textbook ID must start with a digit")
    return textbook


def assign_textbook_id(textbook, used_ids=()):
    """
    Return an ID that can be assigned to a textbook
    and doesn't match the used_ids
    """
    tid = Location.clean(textbook["tab_title"])
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
            upload_asset_url = reverse_course_url('assets_handler', course_key)
            textbook_url = reverse_course_url('textbooks_list_handler', course_key)
            return render_to_response('textbooks.html', {
                'context_course': course,
                'textbooks': course.pdf_textbooks,
                'upload_asset_url': upload_asset_url,
                'textbook_url': textbook_url,
            })

        # from here on down, we know the client has requested JSON
        if request.method == 'GET':
            return JsonResponse(course.pdf_textbooks)
        elif request.method == 'PUT':
            try:
                textbooks = validate_textbooks_json(request.body)
            except TextbookValidationError as err:
                return JsonResponse({"error": err.message}, status=400)

            tids = set(t["id"] for t in textbooks if "id" in t)
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
                return JsonResponse({"error": err.message}, status=400)
            if not textbook.get("id"):
                tids = set(t["id"] for t in course.pdf_textbooks if "id" in t)
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
        course_module = get_course_and_check_access(course_key, request.user)
        matching_id = [tb for tb in course_module.pdf_textbooks
                       if unicode(tb.get("id")) == unicode(textbook_id)]
        if matching_id:
            textbook = matching_id[0]
        else:
            textbook = None

        if request.method == 'GET':
            if not textbook:
                return JsonResponse(status=404)
            return JsonResponse(textbook)
        elif request.method in ('POST', 'PUT'):  # can be either and sometimes
                                            # django is rewriting one to the other
            try:
                new_textbook = validate_textbook_json(request.body)
            except TextbookValidationError as err:
                return JsonResponse({"error": err.message}, status=400)
            new_textbook["id"] = textbook_id
            if textbook:
                i = course_module.pdf_textbooks.index(textbook)
                new_textbooks = course_module.pdf_textbooks[0:i]
                new_textbooks.append(new_textbook)
                new_textbooks.extend(course_module.pdf_textbooks[i + 1:])
                course_module.pdf_textbooks = new_textbooks
            else:
                course_module.pdf_textbooks.append(new_textbook)
            store.update_item(course_module, request.user.id)
            return JsonResponse(new_textbook, status=201)
        elif request.method == 'DELETE':
            if not textbook:
                return JsonResponse(status=404)
            i = course_module.pdf_textbooks.index(textbook)
            remaining_textbooks = course_module.pdf_textbooks[0:i]
            remaining_textbooks.extend(course_module.pdf_textbooks[i + 1:])
            course_module.pdf_textbooks = remaining_textbooks
            store.update_item(course_module, request.user.id)
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
        usages = GroupConfiguration.get_content_groups_usage_info(store, course)
        used = group_id in usages

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
            group_configuration_url = reverse_course_url('group_configurations_list_handler', course_key)
            course_outline_url = reverse_course_url('course_handler', course_key)
            should_show_experiment_groups = are_content_experiments_enabled(course)
            if should_show_experiment_groups:
                experiment_group_configurations = GroupConfiguration.get_split_test_partitions_with_usage(store, course)
            else:
                experiment_group_configurations = None

            content_group_configuration = GroupConfiguration.get_or_create_content_group(store, course)

            return render_to_response('group_configurations.html', {
                'context_course': course,
                'group_configuration_url': group_configuration_url,
                'course_outline_url': course_outline_url,
                'experiment_group_configurations': experiment_group_configurations,
                'should_show_experiment_groups': should_show_experiment_groups,
                'content_group_configuration': content_group_configuration
            })
        elif "application/json" in request.META.get('HTTP_ACCEPT'):
            if request.method == 'POST':
                # create a new group configuration for the course
                try:
                    new_configuration = GroupConfiguration(request.body, course).get_user_partition()
                except GroupConfigurationsValidationError as err:
                    return JsonResponse({"error": err.message}, status=400)

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
                       if unicode(p.id) == unicode(group_configuration_id)]
        if matching_id:
            configuration = matching_id[0]
        else:
            configuration = None

        if request.method in ('POST', 'PUT'):  # can be either and sometimes
                                            # django is rewriting one to the other
            try:
                new_configuration = GroupConfiguration(request.body, course, group_configuration_id).get_user_partition()
            except GroupConfigurationsValidationError as err:
                return JsonResponse({"error": err.message}, status=400)

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


def _get_library_creator_status(user):
    """
    Helper method for returning the library creation status for a particular user,
    taking into account the values of DISABLE_LIBRARY_CREATION and LIBRARIES_ENABLED.
    """
    if user.is_staff:
        library_creator_status = 'granted'
    elif settings.FEATURES.get('DISABLE_LIBRARY_CREATION', False):
        library_creator_status = 'disallowed_for_this_site'
    elif settings.FEATURES.get('ENABLE_CREATOR_GROUP', False):
        library_creator_status = get_course_creator_status(user)
        if library_creator_status is None:
            # User not grandfathered in as an existing user, has not previously visited the dashboard page.
            # Add the user to the course creator admin table with status 'unrequested'.
            add_user_with_status_unrequested(user)
            library_creator_status = get_course_creator_status(user)
    else:
        library_creator_status = 'granted'

    return library_creator_status
