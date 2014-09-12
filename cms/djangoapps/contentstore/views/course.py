"""
Views related to operations on course objects
"""
import json
import random
import string  # pylint: disable=W0402
import logging
from django.utils.translation import ugettext as _
import django.utils
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseBadRequest, HttpResponseNotFound, HttpResponse, Http404
from util.json_request import JsonResponse, JsonResponseBadRequest
from util.date_utils import get_default_time_display
from edxmako.shortcuts import render_to_response

from xmodule.course_module import DEFAULT_START_DATE
from xmodule.error_module import ErrorDescriptor
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.content import StaticContent
from xmodule.tabs import PDFTextbookTabs
from xmodule.partitions.partitions import UserPartition, Group
from xmodule.modulestore import EdxJSONEncoder
from xmodule.modulestore.exceptions import ItemNotFoundError, DuplicateCourseError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locations import Location
from opaque_keys.edx.keys import CourseKey

from django_future.csrf import ensure_csrf_cookie
from contentstore.course_info_model import get_course_updates, update_course_updates, delete_course_update
from contentstore.utils import (
    add_instructor,
    initialize_permissions,
    get_lms_link_for_item,
    add_extra_panel_tab,
    remove_extra_panel_tab,
    reverse_course_url,
    reverse_usage_url,
    reverse_url,
    remove_all_instructors,
)
from models.settings.course_details import CourseDetails, CourseSettingsEncoder
from models.settings.course_grading import CourseGradingModel
from models.settings.course_metadata import CourseMetadata
from util.json_request import expect_json
from util.string_utils import _has_non_ascii_characters
from .access import has_course_access
from .component import (
    OPEN_ENDED_COMPONENT_TYPES,
    NOTE_COMPONENT_TYPES,
    ADVANCED_COMPONENT_POLICY_KEY,
    SPLIT_TEST_COMPONENT_TYPE,
    ADVANCED_COMPONENT_TYPES,
)
from contentstore.tasks import rerun_course
from .item import create_xblock_info
from course_creators.views import get_course_creator_status, add_user_with_status_unrequested
from contentstore import utils
from student.roles import (
    CourseInstructorRole, CourseStaffRole, CourseCreatorRole, GlobalStaff, UserBasedRole
)
from student import auth
from course_action_state.models import CourseRerunState, CourseRerunUIStateManager
from course_action_state.managers import CourseActionStateItemNotFoundError
from microsite_configuration import microsite
from xmodule.course_module import CourseFields


__all__ = ['course_info_handler', 'course_handler', 'course_info_update_handler',
           'course_rerun_handler',
           'settings_handler',
           'grading_handler',
           'advanced_settings_handler',
           'course_notifications_handler',
           'textbooks_list_handler', 'textbooks_detail_handler',
           'group_configurations_list_handler', 'group_configurations_detail_handler']

log = logging.getLogger(__name__)


class AccessListFallback(Exception):
    """
    An exception that is raised whenever we need to `fall back` to fetching *all* courses
    available to a user, rather than using a shorter method (i.e. fetching by group)
    """
    pass


def _get_course_module(course_key, user, depth=0):
    """
    Internal method used to calculate and return the locator and course module
    for the view functions in this file.
    """
    if not has_course_access(user, course_key):
        raise PermissionDenied()
    course_module = modulestore().get_course(course_key, depth=depth)
    return course_module


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

    response_format = request.REQUEST.get('format', 'html')

    course_key = CourseKey.from_string(course_key_string)

    if response_format == 'json' or 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json'):
        if not has_course_access(request.user, course_key):
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
        response_format = request.REQUEST.get('format', 'html')
        if response_format == 'json' or 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json'):
            if request.method == 'GET':
                course_module = _get_course_module(CourseKey.from_string(course_key_string), request.user, depth=None)
                return JsonResponse(_course_outline_json(request, course_module))
            elif request.method == 'POST':  # not sure if this is only post. If one will have ids, it goes after access
                return _create_or_rerun_course(request)
            elif not has_course_access(request.user, CourseKey.from_string(course_key_string)):
                raise PermissionDenied()
            elif request.method == 'PUT':
                raise NotImplementedError()
            elif request.method == 'DELETE':
                raise NotImplementedError()
            else:
                return HttpResponseBadRequest()
        elif request.method == 'GET':  # assume html
            if course_key_string is None:
                return course_listing(request)
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
    course_module = _get_course_module(course_key, request.user, depth=3)
    if request.method == 'GET':
        return render_to_response('course-create-rerun.html', {
            'source_course_key': course_key,
            'display_name': course_module.display_name,
            'user': request.user,
            'course_creator_status': _get_course_creator_status(request.user),
            'allow_unicode_course_id': settings.FEATURES.get('ALLOW_UNICODE_COURSE_ID', False)
        })

def _course_outline_json(request, course_module):
    """
    Returns a JSON representation of the course module and recursively all of its children.
    """
    return create_xblock_info(
        course_module,
        include_child_info=True,
        course_outline=True,
        include_children_predicate=lambda xblock: not xblock.category == 'vertical'
    )


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

        # pylint: disable=fixme
        # TODO remove this condition when templates purged from db
        if course.location.course == 'templates':
            return False

        return has_course_access(request.user, course.id)

    courses = filter(course_filter, modulestore().get_courses())
    in_process_course_actions = [
        course for course in
        CourseRerunState.objects.find_all(
            exclude_args={'state': CourseRerunUIStateManager.State.SUCCEEDED}, should_display=True
        )
        if has_course_access(request.user, course.course_key)
    ]
    return courses, in_process_course_actions


def _accessible_courses_list_from_groups(request):
    """
    List all courses available to the logged in user by reversing access group names
    """
    courses_list = {}
    in_process_course_actions = []

    instructor_courses = UserBasedRole(request.user, CourseInstructorRole.ROLE).courses_with_role()
    staff_courses = UserBasedRole(request.user, CourseStaffRole.ROLE).courses_with_role()
    all_courses = instructor_courses | staff_courses

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
                # ignore deleted or errored courses
                courses_list[course_key] = course

    return courses_list.values(), in_process_course_actions


@login_required
@ensure_csrf_cookie
def course_listing(request):
    """
    List all courses available to the logged in user
    Try to get all courses by first reversing django groups and fallback to old method if it fails
    Note: overhead of pymongo reads will increase if getting courses from django groups fails
    """
    if GlobalStaff().has_user(request.user):
        # user has global access so no need to get courses from django groups
        courses, in_process_course_actions = _accessible_courses_list(request)
    else:
        try:
            courses, in_process_course_actions = _accessible_courses_list_from_groups(request)
        except AccessListFallback:
            # user have some old groups or there was some error getting courses from django groups
            # so fallback to iterating through all courses
            courses, in_process_course_actions = _accessible_courses_list(request)

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
            'dismiss_link':
                reverse_course_url('course_notifications_handler', uca.course_key, kwargs={
                    'action_state_id': uca.id,
                }) if uca.state == CourseRerunUIStateManager.State.FAILED else ''
        }

    # remove any courses in courses that are also in the in_process_course_actions list
    in_process_action_course_keys = [uca.course_key for uca in in_process_course_actions]
    courses = [
        format_course_for_view(c)
        for c in courses
        if not isinstance(c, ErrorDescriptor) and (c.id not in in_process_action_course_keys)
    ]

    in_process_course_actions = [format_in_process_course_view(uca) for uca in in_process_course_actions]

    return render_to_response('index.html', {
        'courses': courses,
        'in_process_course_actions': in_process_course_actions,
        'user': request.user,
        'request_course_creator_url': reverse('contentstore.views.request_course_creator'),
        'course_creator_status': _get_course_creator_status(request.user),
        'rerun_creator_status': GlobalStaff().has_user(request.user),
        'allow_unicode_course_id': settings.FEATURES.get('ALLOW_UNICODE_COURSE_ID', False),
        'allow_course_reruns': settings.FEATURES.get('ALLOW_COURSE_RERUNS', False)
    })


def _get_rerun_link_for_item(course_key):
    """ Returns the rerun link for the given course key. """
    return reverse_course_url('course_rerun_handler', course_key)


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
        course_module = _get_course_module(course_key, request.user, depth=None)
        lms_link = get_lms_link_for_item(course_module.location)
        sections = course_module.get_children()
        course_structure = _course_outline_json(request, course_module)
        locator_to_show = request.REQUEST.get('show', None)
        course_release_date = get_default_time_display(course_module.start) if course_module.start != DEFAULT_START_DATE else _("Unscheduled")
        settings_url = reverse_course_url('settings_handler', course_key)

        try:
            current_action = CourseRerunState.objects.find_first(course_key=course_key, should_display=True)
        except (ItemNotFoundError, CourseActionStateItemNotFoundError):
            current_action = None

        return render_to_response('course_outline.html', {
            'context_course': course_module,
            'lms_link': lms_link,
            'sections': sections,
            'course_structure': course_structure,
            'initial_state': course_outline_initial_state(locator_to_show, course_structure) if locator_to_show else None,
            'course_graders': json.dumps(
                CourseGradingModel.fetch(course_key).graders
            ),
            'rerun_notification_id': current_action.id if current_action else None,
            'course_release_date': course_release_date,
            'settings_url': settings_url,
            'notification_dismiss_url':
                reverse_course_url('course_notifications_handler', current_action.course_key, kwargs={
                    'action_state_id': current_action.id,
                }) if current_action else None,
        })


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
    if not auth.has_access(request.user, CourseCreatorRole()):
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

        if 'source_course_key' in request.json:
            return _rerun_course(request, org, course, run, fields)
        else:
            return _create_new_course(request, org, course, run, fields)

    except DuplicateCourseError:
        return JsonResponse({
            'ErrMsg': _(
                'There is already a course defined with the same '
                'organization, course number, and course run. Please '
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
    # Set a unique wiki_slug for newly created courses. To maintain active wiki_slugs for
    # existing xml courses this cannot be changed in CourseDescriptor.
    # # TODO get rid of defining wiki slug in this org/course/run specific way and reconcile
    # w/ xmodule.course_module.CourseDescriptor.__init__
    wiki_slug = u"{0}.{1}.{2}".format(org, number, run)
    definition_data = {'wiki_slug': wiki_slug}
    fields.update(definition_data)

    store = modulestore()
    store_for_new_course = (
        settings.FEATURES.get('DEFAULT_STORE_FOR_NEW_COURSE') or
        store.default_modulestore.get_modulestore_type()
    )
    with store.default_store(store_for_new_course):
        # Creating the course raises DuplicateCourseError if an existing course with this org/name is found
        new_course = store.create_course(
            org,
            number,
            run,
            request.user.id,
            fields=fields,
        )

    # Make sure user has instructor and staff access to the new course
    add_instructor(new_course.id, request.user, request.user)

    # Initialize permissions for user in the new course
    initialize_permissions(new_course.id, request.user)

    return JsonResponse({
        'url': reverse_course_url('course_handler', new_course.id),
        'course_key': unicode(new_course.id),
    })


def _rerun_course(request, org, number, run, fields):
    """
    Reruns an existing course.
    Returns the URL for the course listing page.
    """
    source_course_key = CourseKey.from_string(request.json.get('source_course_key'))

    # verify user has access to the original course
    if not has_course_access(request.user, source_course_key):
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
    course_key = CourseKey.from_string(course_key_string)
    course_module = _get_course_module(course_key, request.user)
    if 'text/html' in request.META.get('HTTP_ACCEPT', 'text/html'):

        return render_to_response(
            'course_info.html',
            {
                'context_course': course_module,
                'updates_url': reverse_course_url('course_info_update_handler', course_key),
                'handouts_locator': course_key.make_usage_key('course_info', 'handouts'),
                'base_asset_url': StaticContent.get_base_url_path_for_course_assets(course_module.id)
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
    if not has_course_access(request.user, usage_key.course_key):
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
    course_module = _get_course_module(course_key, request.user)
    if 'text/html' in request.META.get('HTTP_ACCEPT', '') and request.method == 'GET':
        upload_asset_url = reverse_course_url('assets_handler', course_key)

        # see if the ORG of this course can be attributed to a 'Microsite'. In that case, the
        # course about page should be editable in Studio
        about_page_editable = not microsite.get_value_for_org(
            course_module.location.org,
            'ENABLE_MKTG_SITE',
            settings.FEATURES.get('ENABLE_MKTG_SITE', False)
        )

        short_description_editable = settings.FEATURES.get('EDITABLE_SHORT_DESCRIPTION', True)

        return render_to_response('settings.html', {
            'context_course': course_module,
            'course_locator': course_key,
            'lms_link_for_about_page': utils.get_lms_link_for_about_page(course_key),
            'course_image_url': utils.course_image_url(course_module),
            'details_url': reverse_course_url('settings_handler', course_key),
            'about_page_editable': about_page_editable,
            'short_description_editable': short_description_editable,
            'upload_asset_url': upload_asset_url
        })
    elif 'application/json' in request.META.get('HTTP_ACCEPT', ''):
        if request.method == 'GET':
            return JsonResponse(
                CourseDetails.fetch(course_key),
                # encoder serializes dates, old locations, and instances
                encoder=CourseSettingsEncoder
            )
        else:  # post or put, doesn't matter.
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
    course_module = _get_course_module(course_key, request.user)

    if 'text/html' in request.META.get('HTTP_ACCEPT', '') and request.method == 'GET':
        course_details = CourseGradingModel.fetch(course_key)

        return render_to_response('settings_graders.html', {
            'context_course': course_module,
            'course_locator': course_key,
            'course_details': json.dumps(course_details, cls=CourseSettingsEncoder),
            'grading_url': reverse_course_url('grading_handler', course_key),
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


# pylint: disable=invalid-name
def _config_course_advanced_components(request, course_module):
    """
    Check to see if the user instantiated any advanced components. This
    is a hack that does the following :
    1) adds/removes the open ended panel tab to a course automatically
    if the user has indicated that they want to edit the
    combinedopendended or peergrading module
    2) adds/removes the notes panel tab to a course automatically if
    the user has indicated that they want the notes module enabled in
    their course
    """
    # TODO refactor the above into distinct advanced policy settings
    filter_tabs = True  # Exceptional conditions will pull this to False
    if ADVANCED_COMPONENT_POLICY_KEY in request.json:  # Maps tab types to components
        tab_component_map = {
            'open_ended': OPEN_ENDED_COMPONENT_TYPES,
            'notes': NOTE_COMPONENT_TYPES,
        }
        # Check to see if the user instantiated any notes or open ended components
        for tab_type in tab_component_map.keys():
            component_types = tab_component_map.get(tab_type)
            found_ac_type = False
            for ac_type in component_types:

                # Check if the user has incorrectly failed to put the value in an iterable.
                new_advanced_component_list = request.json[ADVANCED_COMPONENT_POLICY_KEY]['value']
                if hasattr(new_advanced_component_list, '__iter__'):
                    if ac_type in new_advanced_component_list and ac_type in ADVANCED_COMPONENT_TYPES:

                        # Add tab to the course if needed
                        changed, new_tabs = add_extra_panel_tab(tab_type, course_module)
                        # If a tab has been added to the course, then send the
                        # metadata along to CourseMetadata.update_from_json
                        if changed:
                            course_module.tabs = new_tabs
                            request.json.update({'tabs': {'value': new_tabs}})
                            # Indicate that tabs should not be filtered out of
                            # the metadata
                            filter_tabs = False  # Set this flag to avoid the tab removal code below.
                        found_ac_type = True  # break
                else:
                    # If not iterable, return immediately and let validation handle.
                    return

            # If we did not find a module type in the advanced settings,
            # we may need to remove the tab from the course.
            if not found_ac_type:  # Remove tab from the course if needed
                changed, new_tabs = remove_extra_panel_tab(tab_type, course_module)
                if changed:
                    course_module.tabs = new_tabs
                    request.json.update({'tabs': {'value': new_tabs}})
                    # Indicate that tabs should *not* be filtered out of
                    # the metadata
                    filter_tabs = False

    return filter_tabs


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
    course_module = _get_course_module(course_key, request.user)
    if 'text/html' in request.META.get('HTTP_ACCEPT', '') and request.method == 'GET':

        return render_to_response('settings_advanced.html', {
            'context_course': course_module,
            'advanced_dict': json.dumps(CourseMetadata.fetch(course_module)),
            'advanced_settings_url': reverse_course_url('advanced_settings_handler', course_key)
        })
    elif 'application/json' in request.META.get('HTTP_ACCEPT', ''):
        if request.method == 'GET':
            return JsonResponse(CourseMetadata.fetch(course_module))
        else:
            try:
                # Whether or not to filter the tabs key out of the settings metadata
                filter_tabs = _config_course_advanced_components(request, course_module)

                # validate data formats and update
                is_valid, errors, updated_data = CourseMetadata.validate_and_update_from_json(
                    course_module,
                    request.json,
                    filter_tabs=filter_tabs,
                    user=request.user,
                )

                if is_valid:
                    return JsonResponse(updated_data)
                else:
                    return JsonResponseBadRequest(errors)

            # Handle all errors that validation doesn't catch
            except (TypeError, ValueError) as err:
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
    course = _get_course_module(course_key, request.user)
    store = modulestore()

    if not "application/json" in request.META.get('HTTP_ACCEPT', 'text/html'):
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
            if not "id" in textbook:
                tid = assign_textbook_id(textbook, tids)
                textbook["id"] = tid
                tids.add(tid)

        if not any(tab['type'] == PDFTextbookTabs.type for tab in course.tabs):
            course.tabs.append(PDFTextbookTabs())
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
        if not any(tab['type'] == PDFTextbookTabs.type for tab in course.tabs):
            course.tabs.append(PDFTextbookTabs())
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
    course_module = _get_course_module(course_key, request.user)
    store = modulestore()
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


class GroupConfigurationsValidationError(Exception):
    """
    An error thrown when a group configurations input is invalid.
    """
    pass


class GroupConfiguration(object):
    """
    Prepare Group Configuration for the course.
    """
    def __init__(self, json_string, course, configuration_id=None):
        """
        Receive group configuration as a json (`json_string`), deserialize it
        and validate.
        """
        self.configuration = GroupConfiguration.parse(json_string)
        self.course = course
        self.assign_id(configuration_id)
        self.assign_group_ids()
        self.validate()

    @staticmethod
    def parse(json_string):
        """
        Deserialize given json that represents group configuration.
        """
        try:
            configuration = json.loads(json_string)
        except ValueError:
            raise GroupConfigurationsValidationError(_("invalid JSON"))

        return configuration

    def validate(self):
        """
        Validate group configuration representation.
        """
        if not self.configuration.get("name"):
            raise GroupConfigurationsValidationError(_("must have name of the configuration"))
        if len(self.configuration.get('groups', [])) < 1:
            raise GroupConfigurationsValidationError(_("must have at least one group"))

    def generate_id(self, used_ids):
        """
        Generate unique id for the group configuration.
        If this id is already used, we generate new one.
        """
        cid = random.randint(100, 10 ** 12)

        while cid in used_ids:
            cid = random.randint(100, 10 ** 12)

        return cid

    def assign_id(self, configuration_id=None):
        """
        Assign id for the json representation of group configuration.
        """
        self.configuration['id'] = int(configuration_id) if configuration_id else self.generate_id(self.get_used_ids())

    def assign_group_ids(self):
        """
        Assign ids for the group_configuration's groups.
        """
        used_ids = [g.id for p in self.course.user_partitions for g in p.groups]
        # Assign ids to every group in configuration.
        for group in self.configuration.get('groups', []):
            if group.get('id') is None:
                group["id"] = self.generate_id(used_ids)
                used_ids.append(group["id"])

    def get_used_ids(self):
        """
        Return a list of IDs that already in use.
        """
        return set([p.id for p in self.course.user_partitions])

    def get_user_partition(self):
        """
        Get user partition for saving in course.
        """
        groups = [Group(g["id"], g["name"]) for g in self.configuration["groups"]]

        return UserPartition(
            self.configuration["id"],
            self.configuration["name"],
            self.configuration["description"],
            groups
        )

    @staticmethod
    def get_usage_info(course, store):
        """
        Get usage information for all Group Configurations.
        """
        split_tests = store.get_items(course.id, qualifiers={'category': 'split_test'})
        return GroupConfiguration._get_usage_info(store, course, split_tests)

    @staticmethod
    def add_usage_info(course, store):
        """
        Add usage information to group configurations jsons in course.

        Returns json of group configurations updated with usage information.
        """
        usage_info = GroupConfiguration.get_usage_info(course, store)
        configurations = []
        for partition in course.user_partitions:
            configuration = partition.to_json()
            configuration['usage'] = usage_info.get(partition.id, [])
            configurations.append(configuration)
        return configurations

    @staticmethod
    def _get_usage_info(store, course, split_tests):
        """
        Returns all units names, their urls and validation messages.

        Returns:
        {'user_partition_id':
            [
                {
                    'label': 'Unit 1 / Experiment 1',
                    'url': 'url_to_unit_1',
                    'validation': {'message': 'a validation message', 'type': 'warning'}
                },
                {
                    'label': 'Unit 2 / Experiment 2',
                    'url': 'url_to_unit_2',
                    'validation': {'message': 'another validation message', 'type': 'error'}
                }
            ],
        }
        """
        usage_info = {}
        for split_test in split_tests:
            if split_test.user_partition_id not in usage_info:
                usage_info[split_test.user_partition_id] = []

            unit_location = store.get_parent_location(split_test.location)
            if not unit_location:
                log.warning("Parent location of split_test module not found: %s", split_test.location)
                continue

            try:
                unit = store.get_item(unit_location)
            except ItemNotFoundError:
                log.warning("Unit not found: %s", unit_location)
                continue

            unit_url = reverse_usage_url(
                'container_handler',
                course.location.course_key.make_usage_key(unit.location.block_type, unit.location.name)
            )
            usage_info[split_test.user_partition_id].append({
                'label': '{} / {}'.format(unit.display_name, split_test.display_name),
                'url': unit_url,
                'validation': split_test.general_validation_message,
            })
        return usage_info

    @staticmethod
    def update_usage_info(store, course, configuration):
        """
        Update usage information for particular Group Configuration.

        Returns json of particular group configuration updated with usage information.
        """
        # Get all Experiments that use particular Group Configuration in course.
        split_tests = store.get_items(
            course.id,
            category='split_test',
            content={'user_partition_id': configuration.id}
        )
        configuration_json = configuration.to_json()
        usage_information = GroupConfiguration._get_usage_info(store, course, split_tests)
        configuration_json['usage'] = usage_information.get(configuration.id, [])
        return configuration_json


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
    course = _get_course_module(course_key, request.user)
    store = modulestore()

    if 'text/html' in request.META.get('HTTP_ACCEPT', 'text/html'):
        group_configuration_url = reverse_course_url('group_configurations_list_handler', course_key)
        course_outline_url = reverse_course_url('course_handler', course_key)
        split_test_enabled = SPLIT_TEST_COMPONENT_TYPE in ADVANCED_COMPONENT_TYPES and SPLIT_TEST_COMPONENT_TYPE in course.advanced_modules

        configurations = GroupConfiguration.add_usage_info(course, store)

        return render_to_response('group_configurations.html', {
            'context_course': course,
            'group_configuration_url': group_configuration_url,
            'course_outline_url': course_outline_url,
            'configurations': configurations if split_test_enabled else None,
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
                kwargs={'group_configuration_id': new_configuration.id}  # pylint: disable=no-member
            )
            store.update_item(course, request.user.id)
            return response
    else:
        return HttpResponse(status=406)


@login_required
@ensure_csrf_cookie
@require_http_methods(("POST", "PUT", "DELETE"))
def group_configurations_detail_handler(request, course_key_string, group_configuration_id):
    """
    JSON API endpoint for manipulating a group configuration via its internal ID.
    Used by the Backbone application.

    POST or PUT
        json: update group configuration based on provided information
    """
    course_key = CourseKey.from_string(course_key_string)
    course = _get_course_module(course_key, request.user)
    store = modulestore()
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

        # Verify that group configuration is not already in use.
        usages = GroupConfiguration.get_usage_info(course, store)
        if usages.get(int(group_configuration_id)):
            return JsonResponse(
                {"error": _("This Group Configuration is already in use and cannot be removed.")},
                status=400
            )

        index = course.user_partitions.index(configuration)
        course.user_partitions.pop(index)
        store.update_item(course, request.user.id)
        return JsonResponse(status=204)


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
