"""
Views related to operations on course objects
"""
import json
import random
import string  # pylint: disable=W0402

from django.utils.translation import ugettext as _
import django.utils
from django.contrib.auth.decorators import login_required
from django_future.csrf import ensure_csrf_cookie
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseBadRequest, HttpResponseNotFound
from util.json_request import JsonResponse
from edxmako.shortcuts import render_to_response

from xmodule.error_module import ErrorDescriptor
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.content import StaticContent
from xmodule.tabs import PDFTextbookTabs

from xmodule.modulestore.exceptions import ItemNotFoundError, InvalidLocationError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locations import Location, SlashSeparatedCourseKey

from contentstore.course_info_model import get_course_updates, update_course_updates, delete_course_update
from contentstore.utils import (
    get_lms_link_for_item,
    add_extra_panel_tab,
    remove_extra_panel_tab,
    reverse_course_url
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
)

from django_comment_common.models import assign_default_role
from django_comment_common.utils import seed_permissions_roles

from student.models import CourseEnrollment
from student.roles import CourseRole, UserBasedRole

from opaque_keys.edx.keys import CourseKey
from course_creators.views import get_course_creator_status, add_user_with_status_unrequested
from contentstore import utils
from student.roles import CourseInstructorRole, CourseStaffRole, CourseCreatorRole, GlobalStaff
from student import auth

from microsite_configuration import microsite

__all__ = ['course_info_handler', 'course_handler', 'course_info_update_handler',
           'settings_handler',
           'grading_handler',
           'advanced_settings_handler',
           'textbooks_list_handler', 'textbooks_detail_handler',
           'group_configurations_list_handler']


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
        offering. Return same json as above.
    DELETE
        json: delete this branch from this course (leaving off /branch/draft would imply delete the course)
    """
    response_format = request.REQUEST.get('format', 'html')
    if response_format == 'json' or 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json'):
        if request.method == 'GET':
            return JsonResponse(_course_json(request, CourseKey.from_string(course_key_string)))
        elif request.method == 'POST':  # not sure if this is only post. If one will have ids, it goes after access
            return create_new_course(request)
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


@login_required
def _course_json(request, course_key):
    """
    Returns a JSON overview of a course
    """
    course_module = _get_course_module(course_key, request.user, depth=None)
    return _xmodule_json(course_module, course_module.id)


def _xmodule_json(xmodule, course_id):
    """
    Returns a JSON overview of an XModule
    """
    is_container = xmodule.has_children
    result = {
        'display_name': xmodule.display_name,
        'id': unicode(xmodule.location),
        'category': xmodule.category,
        'is_draft': getattr(xmodule, 'is_draft', False),
        'is_container': is_container,
    }
    if is_container:
        result['children'] = [_xmodule_json(child, course_id) for child in xmodule.get_children()]
    return result


def _accessible_courses_list(request):
    """
    List all courses available to the logged in user by iterating through all the courses
    """
    courses = modulestore().get_courses()

    # filter out courses that we don't have access to
    def course_filter(course):
        """
        Get courses to which this user has access
        """
        if isinstance(course, ErrorDescriptor):
            return False

        if GlobalStaff().has_user(request.user):
            return course.location.course != 'templates'

        return (has_course_access(request.user, course.id)
                # pylint: disable=fixme
                # TODO remove this condition when templates purged from db
                and course.location.course != 'templates'
                )
    courses = filter(course_filter, courses)
    return courses


def _accessible_courses_list_from_groups(request):
    """
    List all courses available to the logged in user by reversing access group names
    """
    courses_list = {}

    instructor_courses = UserBasedRole(request.user, CourseInstructorRole.ROLE).courses_with_role()
    staff_courses = UserBasedRole(request.user, CourseStaffRole.ROLE).courses_with_role()
    all_courses = instructor_courses | staff_courses

    for course_access in all_courses:
        course_key = course_access.course_id
        if course_key is None:
            # If the course_access does not have a course_id, it's an org-based role, so we fall back
            raise AccessListFallback
        if course_key not in courses_list:
            try:
                course = modulestore().get_course(course_key)
            except ItemNotFoundError:
                # If a user has access to a course that doesn't exist, don't do anything with that course
                pass
            if course is not None and not isinstance(course, ErrorDescriptor):
                # ignore deleted or errored courses
                courses_list[course_key] = course

    return courses_list.values()


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
        courses = _accessible_courses_list(request)
    else:
        try:
            courses = _accessible_courses_list_from_groups(request)
        except AccessListFallback:
            # user have some old groups or there was some error getting courses from django groups
            # so fallback to iterating through all courses
            courses = _accessible_courses_list(request)

    def format_course_for_view(course):
        """
        return tuple of the data which the view requires for each course
        """
        return (
            course.display_name,
            reverse_course_url('course_handler', course.id),
            get_lms_link_for_item(course.location),
            course.display_org_with_default,
            course.display_number_with_default,
            course.location.name
        )

    return render_to_response('index.html', {
        'courses': [format_course_for_view(c) for c in courses if not isinstance(c, ErrorDescriptor)],
        'user': request.user,
        'request_course_creator_url': reverse('contentstore.views.request_course_creator'),
        'course_creator_status': _get_course_creator_status(request.user),
        'allow_unicode_course_id': settings.FEATURES.get('ALLOW_UNICODE_COURSE_ID', False)
    })


@login_required
@ensure_csrf_cookie
def course_index(request, course_key):
    """
    Display an editable course overview.

    org, course, name: Attributes of the Location for the item to edit
    """
    course_module = _get_course_module(course_key, request.user, depth=3)
    lms_link = get_lms_link_for_item(course_module.location)
    sections = course_module.get_children()

    return render_to_response('overview.html', {
        'context_course': course_module,
        'lms_link': lms_link,
        'sections': sections,
        'course_graders': json.dumps(
            CourseGradingModel.fetch(course_key).graders
        ),
        'new_section_category': 'chapter',
        'new_subsection_category': 'sequential',
        'new_unit_category': 'vertical',
        'category': 'vertical'
    })


@expect_json
def create_new_course(request):
    """
    Create a new course.

    Returns the URL for the course overview page.
    """
    if not auth.has_access(request.user, CourseCreatorRole()):
        raise PermissionDenied()

    org = request.json.get('org')
    number = request.json.get('number')
    display_name = request.json.get('display_name')
    run = request.json.get('run')

    # allow/disable unicode characters in course_id according to settings
    if not settings.FEATURES.get('ALLOW_UNICODE_COURSE_ID'):
        if _has_non_ascii_characters(org) or _has_non_ascii_characters(number) or _has_non_ascii_characters(run):
            return JsonResponse(
                {'error': _('Special characters not allowed in organization, course number, and course run.')},
                status=400
            )

    try:
        course_key = SlashSeparatedCourseKey(org, number, run)

        # instantiate the CourseDescriptor and then persist it
        # note: no system to pass
        if display_name is None:
            metadata = {}
        else:
            metadata = {'display_name': display_name}

        # Set a unique wiki_slug for newly created courses. To maintain active wiki_slugs for
        # existing xml courses this cannot be changed in CourseDescriptor.
        # # TODO get rid of defining wiki slug in this org/course/run specific way and reconcile
        # w/ xmodule.course_module.CourseDescriptor.__init__
        wiki_slug = u"{0}.{1}.{2}".format(course_key.org, course_key.course, course_key.run)
        definition_data = {'wiki_slug': wiki_slug}

        # Create the course then fetch it from the modulestore
        # Check if role permissions group for a course named like this already exists
        # Important because role groups are case insensitive
        if CourseRole.course_group_already_exists(course_key):
            raise InvalidLocationError()

        fields = {}
        fields.update(definition_data)
        fields.update(metadata)

        # Creating the course raises InvalidLocationError if an existing course with this org/name is found
        new_course = modulestore().create_course(
            course_key.org,
            course_key.offering,
            fields=fields,
        )

        # can't use auth.add_users here b/c it requires request.user to already have Instructor perms in this course
        # however, we can assume that b/c this user had authority to create the course, the user can add themselves
        CourseInstructorRole(new_course.id).add_users(request.user)
        auth.add_users(request.user, CourseStaffRole(new_course.id), request.user)

        # seed the forums
        seed_permissions_roles(new_course.id)

        # auto-enroll the course creator in the course so that "View Live" will
        # work.
        CourseEnrollment.enroll(request.user, new_course.id)
        _users_assign_default_role(new_course.id)

        return JsonResponse({
            'url': reverse_course_url('course_handler', new_course.id)
        })

    except InvalidLocationError:
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


def _users_assign_default_role(course_id):
    """
    Assign 'Student' role to all previous users (if any) for this course
    """
    enrollments = CourseEnrollment.objects.filter(course_id=course_id)
    for enrollment in enrollments:
        assign_default_role(course_id, enrollment.user)


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
                if ac_type in request.json[ADVANCED_COMPONENT_POLICY_KEY]["value"]:
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
                return JsonResponse(CourseMetadata.update_from_json(
                    course_module,
                    request.json,
                    filter_tabs=filter_tabs,
                    user=request.user,
                ))
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


@require_http_methods(("GET"))
@login_required
@ensure_csrf_cookie
def group_configurations_list_handler(request, course_key_string):
    """
    A RESTful handler for Group Configurations

    GET
        html: return Group Configurations list page (Backbone application)
    """
    course_key = CourseKey.from_string(course_key_string)
    course = _get_course_module(course_key, request.user)
    group_configuration_url = reverse_course_url('group_configurations_list_handler', course_key)
    splite_test_enabled = SPLIT_TEST_COMPONENT_TYPE in course.advanced_modules

    return render_to_response('group_configurations.html', {
        'context_course': course,
        'group_configuration_url': group_configuration_url,
        'configurations': [u.to_json() for u in course.user_partitions] if splite_test_enabled else None,
    })


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
