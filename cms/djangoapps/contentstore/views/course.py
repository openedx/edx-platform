"""
Views related to operations on course objects
"""
import json
import random
import string  # pylint: disable=W0402
import re
import bson

from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django_future.csrf import ensure_csrf_cookie
from django.conf import settings
from django.views.decorators.http import require_http_methods, require_POST
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseBadRequest, HttpResponseNotFound
from util.json_request import JsonResponse
from mitxmako.shortcuts import render_to_response

from xmodule.error_module import ErrorDescriptor
from xmodule.modulestore.django import modulestore, loc_mapper
from xmodule.modulestore.inheritance import own_metadata
from xmodule.contentstore.content import StaticContent

from xmodule.modulestore.exceptions import (
    ItemNotFoundError, InvalidLocationError)
from xmodule.modulestore import Location

from contentstore.course_info_model import (
    get_course_updates, update_course_updates, delete_course_update)
from contentstore.utils import (
    get_lms_link_for_item, add_extra_panel_tab, remove_extra_panel_tab,
    get_modulestore)
from models.settings.course_details import (
    CourseDetails, CourseSettingsEncoder)

from models.settings.course_grading import CourseGradingModel
from models.settings.course_metadata import CourseMetadata
from auth.authz import create_all_course_groups, is_user_in_creator_group
from util.json_request import expect_json

from .access import has_access, get_location_and_verify_access
from .tabs import initialize_course_tabs
from .component import (
    OPEN_ENDED_COMPONENT_TYPES, NOTE_COMPONENT_TYPES,
    ADVANCED_COMPONENT_POLICY_KEY)

from django_comment_common.utils import seed_permissions_roles

from student.models import CourseEnrollment

from xmodule.html_module import AboutDescriptor
from xmodule.modulestore.locator import BlockUsageLocator
from course_creators.views import get_course_creator_status, add_user_with_status_unrequested
import pdb

__all__ = ['course_info_handler', 'course_handler', 'course_info_update_handler',
           'get_course_settings',
           'course_config_graders_page',
           'course_config_advanced_page',
           'course_settings_updates',
           'course_grader_updates',
           'course_advanced_updates',
           'syllabus','textbook_index', 'textbook_by_id', 'syllabus_by_id',
           'create_textbook', 'create_syllabus']
# pylint: disable=unused-argument
@login_required
def course_handler(request, tag=None, course_id=None, branch=None, version_guid=None, block=None):
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
        course_id, prettyid. Return same json as above.
    DELETE
        json: delete this branch from this course (leaving off /branch/draft would imply delete the course)
    """
    if 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json'):
        if request.method == 'GET':
            raise NotImplementedError('coming soon')
        elif request.method == 'POST':  # not sure if this is only post. If one will have ids, it goes after access
            return create_new_course(request)
        elif not has_access(
            request.user,
            BlockUsageLocator(course_id=course_id, branch=branch, version_guid=version_guid, usage_id=block)
        ):
            raise PermissionDenied()
        elif request.method == 'PUT':
            raise NotImplementedError()
        elif request.method == 'DELETE':
            raise NotImplementedError()
        else:
            return HttpResponseBadRequest()
    elif request.method == 'GET':  # assume html
        if course_id is None:
            return course_listing(request)
        else:
            return course_index(request, course_id, branch, version_guid, block)
    else:
        return HttpResponseNotFound()


@login_required
@ensure_csrf_cookie
def course_listing(request):
    """
    List all courses available to the logged in user
    """
    courses = modulestore('direct').get_items(['i4x', None, None, 'course', None])

    # filter out courses that we don't have access too
    def course_filter(course):
        """
        Get courses to which this user has access
        """
        return (has_access(request.user, course.location)
                # pylint: disable=fixme
                # TODO remove this condition when templates purged from db
                and course.location.course != 'templates'
                and course.location.org != ''
                and course.location.course != ''
                and course.location.name != '')
    courses = filter(course_filter, courses)

    def format_course_for_view(course):
        """
        return tuple of the data which the view requires for each course
        """
        # published = false b/c studio manipulates draft versions not b/c the course isn't pub'd
        course_loc = loc_mapper().translate_location(
            course.location.course_id, course.location, published=False, add_entry_if_missing=True
        )
        return (
            course.display_name,
            # note, couldn't get django reverse to work; so, wrote workaround
            course_loc.url_reverse('course/', ''),
            get_lms_link_for_item(
                course.location
            ),
            course.display_org_with_default,
            course.display_number_with_default,
            course.location.name
        )

    return render_to_response('index.html', {
        'courses': [format_course_for_view(c) for c in courses if not isinstance(c, ErrorDescriptor)],
        'user': request.user,
        'request_course_creator_url': reverse('contentstore.views.request_course_creator'),
        'course_creator_status': _get_course_creator_status(request.user),
    })


@login_required
@ensure_csrf_cookie
def course_index(request, course_id, branch, version_guid, block):
    """
    Display an editable course overview.

    org, course, name: Attributes of the Location for the item to edit
    """
    location = BlockUsageLocator(course_id=course_id, branch=branch, version_guid=version_guid, usage_id=block)
    # TODO: when converting to split backend, if location does not have a usage_id,
    # we'll need to get the course's root block_id
    if not has_access(request.user, location):
        raise PermissionDenied()


    old_location = loc_mapper().translate_locator_to_location(location)

    lms_link = get_lms_link_for_item(old_location)

    course = modulestore().get_item(old_location, depth=3)
    sections = course.get_children()

    return render_to_response('overview.html', {
        'context_course': course,
        'lms_link': lms_link,
        'sections': sections,
        'course_graders': json.dumps(
            CourseGradingModel.fetch(course.location).graders
        ),
        'parent_location': course.location,
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
    if not is_user_in_creator_group(request.user):
        raise PermissionDenied()

    org = request.json.get('org')
    number = request.json.get('number')
    display_name = request.json.get('display_name')
    run = request.json.get('run')

    try:
        dest_location = Location('i4x', org, number, 'course', run)
    except InvalidLocationError as error:
        return JsonResponse({
            "ErrMsg": _("Unable to create course '{name}'.\n\n{err}").format(
                name=display_name, err=error.message)})

    # see if the course already exists
    existing_course = None
    try:
        existing_course = modulestore('direct').get_item(dest_location)
    except ItemNotFoundError:
        pass
    if existing_course is not None:
        return JsonResponse({
            'ErrMsg': _('There is already a course defined with the same '
                'organization, course number, and course run. Please '
                'change either organization or course number to be '
                'unique.'),
            'OrgErrMsg': _('Please change either the organization or '
                'course number so that it is unique.'),
            'CourseErrMsg': _('Please change either the organization or '
                'course number so that it is unique.'),
        })

    # dhm: this query breaks the abstraction, but I'll fix it when I do my suspended refactoring of this
    # file for new locators. get_items should accept a query rather than requiring it be a legal location
    course_search_location = bson.son.SON({
        '_id.tag': 'i4x',
        # cannot pass regex to Location constructor; thus this hack
        '_id.org': re.compile('^{}$'.format(dest_location.org), re.IGNORECASE),
        '_id.course': re.compile('^{}$'.format(dest_location.course), re.IGNORECASE),
        '_id.category': 'course',
    })
    courses = modulestore().collection.find(course_search_location, fields=('_id'))
    if courses.count() > 0:
        return JsonResponse({
            'ErrMsg': _('There is already a course defined with the same '
                'organization and course number. Please '
                'change at least one field to be unique.'),
            'OrgErrMsg': _('Please change either the organization or '
                'course number so that it is unique.'),
            'CourseErrMsg': _('Please change either the organization or '
                'course number so that it is unique.'),
        })

    # instantiate the CourseDescriptor and then persist it
    # note: no system to pass
    if display_name is None:
        metadata = {}
    else:
        metadata = {'display_name': display_name}
    modulestore('direct').create_and_save_xmodule(
        dest_location,
        metadata=metadata
    )
    new_course = modulestore('direct').get_item(dest_location)

    # clone a default 'about' overview module as well
    dest_about_location = dest_location.replace(
        category='about',
        name='overview'
    )
    overview_template = AboutDescriptor.get_template('overview.yaml')
    modulestore('direct').create_and_save_xmodule(
        dest_about_location,
        system=new_course.system,
        definition_data=overview_template.get('data')
    )

    initialize_course_tabs(new_course)

    create_all_course_groups(request.user, new_course.location)

    # seed the forums
    seed_permissions_roles(new_course.location.course_id)

    # auto-enroll the course creator in the course so that "View Live" will
    # work.
    CourseEnrollment.enroll(request.user, new_course.location.course_id)

    new_location = loc_mapper().translate_location(new_course.location.course_id, new_course.location, False, True)
    return JsonResponse({'url': new_location.url_reverse("course/", "")})


# pylint: disable=unused-argument
@login_required
@ensure_csrf_cookie
@require_http_methods(["GET"])
def course_info_handler(request, tag=None, course_id=None, branch=None, version_guid=None, block=None):
    """
    GET
        html: return html for editing the course info handouts and updates.
    """
    course_location = BlockUsageLocator(course_id=course_id, branch=branch, version_guid=version_guid, usage_id=block)
    course_old_location = loc_mapper().translate_locator_to_location(course_location)
    if 'text/html' in request.META.get('HTTP_ACCEPT', 'text/html'):
        if not has_access(request.user, course_location):
            raise PermissionDenied()

        course_module = modulestore().get_item(course_old_location)

        handouts_old_location = course_old_location.replace(category='course_info', name='handouts')
        handouts_locator = loc_mapper().translate_location(
            course_old_location.course_id, handouts_old_location, False, True
        )

        update_location = course_old_location.replace(category='course_info', name='updates')
        update_locator = loc_mapper().translate_location(
            course_old_location.course_id, update_location, False, True
        )

        return render_to_response(
            'course_info.html',
            {
                'context_course': course_module,
                'updates_url': update_locator.url_reverse('course_info_update/'),
                'handouts_locator': handouts_locator,
                'base_asset_url': StaticContent.get_base_url_path_for_course_assets(course_old_location) + '/'
            }
        )
    else:
        return HttpResponseBadRequest("Only supports html requests")


# pylint: disable=unused-argument
@login_required
@ensure_csrf_cookie
@require_http_methods(("GET", "POST", "PUT", "DELETE"))
@expect_json
def course_info_update_handler(
    request, tag=None, course_id=None, branch=None, version_guid=None, block=None, provided_id=None
    ):
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
    updates_locator = BlockUsageLocator(course_id=course_id, branch=branch, version_guid=version_guid, usage_id=block)
    updates_location = loc_mapper().translate_locator_to_location(updates_locator)
    if provided_id == '':
        provided_id = None

    # check that logged in user has permissions to this item (GET shouldn't require this level?)
    if not has_access(request.user, updates_location):
        raise PermissionDenied()

    if request.method == 'GET':
        return JsonResponse(get_course_updates(updates_location, provided_id))
    elif request.method == 'DELETE':
        try:
            return JsonResponse(delete_course_update(updates_location, request.json, provided_id))
        except:
            return HttpResponseBadRequest(
                "Failed to delete",
                content_type="text/plain"
            )
    # can be either and sometimes django is rewriting one to the other:
    elif request.method in ('POST', 'PUT'):
        try:
            return JsonResponse(update_course_updates(updates_location, request.json, provided_id))
        except:
            return HttpResponseBadRequest(
                "Failed to save",
                content_type="text/plain"
            )


@login_required
@ensure_csrf_cookie
def get_course_settings(request, org, course, name):
    """
    Send models and views as well as html for editing the course settings to
    the client.

    org, course, name: Attributes of the Location for the item to edit
    """
    location = get_location_and_verify_access(request, org, course, name)

    course_module = modulestore().get_item(location)

    new_loc = loc_mapper().translate_location(location.course_id, location, False, True)
    upload_asset_url = new_loc.url_reverse('assets/', '')

    return render_to_response('settings.html', {
        'context_course': course_module,
        'course_location': location,
        'details_url': reverse(course_settings_updates,
                               kwargs={"org": org,
                                       "course": course,
                                       "name": name,
                                       "section": "details"}),
        'about_page_editable': not settings.MITX_FEATURES.get(
            'ENABLE_MKTG_SITE', False
        ),
        'upload_asset_url': upload_asset_url
    })


@login_required
@ensure_csrf_cookie
def course_config_graders_page(request, org, course, name):
    """
    Send models and views as well as html for editing the course settings to
    the client.

    org, course, name: Attributes of the Location for the item to edit
    """
    location = get_location_and_verify_access(request, org, course, name)

    course_module = modulestore().get_item(location)
    course_details = CourseGradingModel.fetch(location)

    return render_to_response('settings_graders.html', {
        'context_course': course_module,
        'course_location': location,
        'course_details': json.dumps(course_details, cls=CourseSettingsEncoder)
    })


@login_required
@ensure_csrf_cookie
def course_config_advanced_page(request, org, course, name):
    """
    Send models and views as well as html for editing the advanced course
    settings to the client.

    org, course, name: Attributes of the Location for the item to edit
    """
    location = get_location_and_verify_access(request, org, course, name)

    course_module = modulestore().get_item(location)

    return render_to_response('settings_advanced.html', {
        'context_course': course_module,
        'course_location': location,
        'advanced_dict': json.dumps(CourseMetadata.fetch(location)),
    })


@expect_json
@login_required
@ensure_csrf_cookie
def course_settings_updates(request, org, course, name, section):
    """
    Restful CRUD operations on course settings. This differs from
    get_course_settings by communicating purely through json (not rendering any
    html) and handles section level operations rather than whole page.

    org, course: Attributes of the Location for the item to edit
    section: one of details, faculty, grading, problems, discussions
    """
    get_location_and_verify_access(request, org, course, name)

    if section == 'details':
        manager = CourseDetails
    elif section == 'grading':
        manager = CourseGradingModel
    else:
        return

    if request.method == 'GET':
        # Cannot just do a get w/o knowing the course name :-(
        return JsonResponse(
            manager.fetch(Location(['i4x', org, course, 'course', name])),
            encoder=CourseSettingsEncoder
        )
    elif request.method in ('POST', 'PUT'):  # post or put, doesn't matter.
        return JsonResponse(
            manager.update_from_json(request.json),
            encoder=CourseSettingsEncoder
        )


@expect_json
@require_http_methods(("GET", "POST", "PUT", "DELETE"))
@login_required
@ensure_csrf_cookie
def course_grader_updates(request, org, course, name, grader_index=None):
    """
    Restful CRUD operations on course_info updates. This differs from
    get_course_settings by communicating purely through json (not rendering any
    html) and handles section level operations rather than whole page.

    org, course: Attributes of the Location for the item to edit
    """

    location = get_location_and_verify_access(request, org, course, name)

    if request.method == 'GET':
        # Cannot just do a get w/o knowing the course name :-(
        return JsonResponse(CourseGradingModel.fetch_grader(
            Location(location), grader_index
        ))
    elif request.method == "DELETE":
        # ??? Should this return anything? Perhaps success fail?
        CourseGradingModel.delete_grader(Location(location), grader_index)
        return JsonResponse()
    else:  # post or put, doesn't matter.
        return JsonResponse(CourseGradingModel.update_grader_from_json(
            Location(location),
            request.json
        ))


@require_http_methods(("GET", "POST", "PUT", "DELETE"))
@login_required
@ensure_csrf_cookie
@expect_json
def course_advanced_updates(request, org, course, name):
    """
    Restful CRUD operations on metadata. The payload is a json rep of the
    metadata dicts. For delete, otoh, the payload is either a key or a list of
    keys to delete.

    org, course: Attributes of the Location for the item to edit
    """
    location = get_location_and_verify_access(request, org, course, name)

    if request.method == 'GET':
        return JsonResponse(CourseMetadata.fetch(location))
    elif request.method == 'DELETE':
        return JsonResponse(CourseMetadata.delete_key(
            location,
            json.loads(request.body)
        ))
    else:
        # Whether or not to filter the tabs key out of the settings metadata
        filter_tabs = True

        # Check to see if the user instantiated any advanced components. This
        # is a hack that does the following :
        #   1) adds/removes the open ended panel tab to a course automatically
        #   if the user has indicated that they want to edit the
        #   combinedopendended or peergrading module
        #   2) adds/removes the notes panel tab to a course automatically if
        #   the user has indicated that they want the notes module enabled in
        #   their course
        # TODO refactor the above into distinct advanced policy settings
        if ADVANCED_COMPONENT_POLICY_KEY in request.json:
            # Get the course so that we can scrape current tabs
            course_module = modulestore().get_item(location)

            # Maps tab types to components
            tab_component_map = {
                'open_ended': OPEN_ENDED_COMPONENT_TYPES,
                'notes': NOTE_COMPONENT_TYPES,
            }

            # Check to see if the user instantiated any notes or open ended
            # components
            for tab_type in tab_component_map.keys():
                component_types = tab_component_map.get(tab_type)
                found_ac_type = False
                for ac_type in component_types:
                    if ac_type in request.json[ADVANCED_COMPONENT_POLICY_KEY]:
                        # Add tab to the course if needed
                        changed, new_tabs = add_extra_panel_tab(
                            tab_type,
                            course_module
                        )
                        # If a tab has been added to the course, then send the
                        # metadata along to CourseMetadata.update_from_json
                        if changed:
                            course_module.tabs = new_tabs
                            request.json.update({'tabs': new_tabs})
                            # Indicate that tabs should not be filtered out of
                            # the metadata
                            filter_tabs = False
                        # Set this flag to avoid the tab removal code below.
                        found_ac_type = True
                        break
                # If we did not find a module type in the advanced settings,
                # we may need to remove the tab from the course.
                if not found_ac_type:
                    # Remove tab from the course if needed
                    changed, new_tabs = remove_extra_panel_tab(
                        tab_type, course_module
                    )
                    if changed:
                        course_module.tabs = new_tabs
                        request.json.update({'tabs': new_tabs})
                        # Indicate that tabs should *not* be filtered out of
                        # the metadata
                        filter_tabs = False
        try:
            return JsonResponse(CourseMetadata.update_from_json(
                location,
                request.json,
                filter_tabs=filter_tabs
            ))
        except (TypeError, ValueError) as err:
            return HttpResponseBadRequest(
                "Incorrect setting format. " + str(err),
                content_type="text/plain"
            )


class TextbookValidationError(Exception):
    "An error thrown when a textbook input is invalid"
    pass

class SyllabusValidationError(Exception):
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
    tid = str(textbook.get("id", ""))
    if tid and not tid[0].isdigit():
        raise TextbookValidationError("textbook ID must start with a digit")
    return textbook

def validate_syllabus_json(syllabus):
    """
    Validate the given text as representing a list of PDF textbooks
    """
    if isinstance(syllabus, basestring):
        try:
            syllabus = json.loads(syllabus)
        except ValueError:
            raise SyllabusValidationError("invalid JSON")
    if not isinstance(syllabus, dict):
        raise SyllabusValidationError("must be JSON object")
    if not syllabus.get("tab_title"):
        raise SyllabusValidationError("must have tab_title")
    tid = str(syllabus.get("id", ""))
    if tid and not tid[0].isdigit():
        raise SyllabusValidationError("syllabus ID must start with a digit")
    return syllabus


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

def assign_syllabus_id(syllabus, used_ids=()):
    """
    Return an ID that can be assigned to a textbook
    and doesn't match the used_ids
    """
    tid = Location.clean(syllabus["tab_title"])
    if not tid[0].isdigit():
        # stick a random digit in front
        tid = random.choice(string.digits) + tid
    while tid in used_ids:
        # add a random ASCII character to the end
        tid = tid + random.choice(string.ascii_lowercase)
    return tid

@login_required
@ensure_csrf_cookie
def syllabus(request, org, course, name):
    """
    Display an editable syllabus.

    org, course, name: Attributes of the Location for the item to edit
    """
    location = get_location_and_verify_access(request, org, course, name)
    store = get_modulestore(location)
    course_module = store.get_item(location, depth=3)

    
    new_loc = loc_mapper().translate_location(location.course_id, location, False, True)
    upload_asset_url = new_loc.url_reverse('assets/', '')
    syllabus_url = reverse('syllabus', kwargs={
        'org': org,
        'course': course,
        'name': name,
    })
    return render_to_response('syllabus.html', {
        'context_course': course_module,
        'course': course_module,
        'syllabus_url': syllabus_url,
    })

@login_required
@ensure_csrf_cookie
def textbook_index(request, org, course, name):
    """
    Display an editable textbook overview.

    org, course, name: Attributes of the Location for the item to edit
    """

    location = get_location_and_verify_access(request, org, course, name)
    store = get_modulestore(location)
    course_module = store.get_item(location, depth=3)

    if request.is_ajax():
        if request.method == 'GET':
            return JsonResponse(course_module.pdf_textbooks)
        # can be either and sometimes django is rewriting one to the other:
        elif request.method in ('POST', 'PUT'):
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

            if not any(tab['type'] == 'pdf_textbooks' for tab in course_module.tabs):
                course_module.tabs.append({"type": "pdf_textbooks"})
            course_module.pdf_textbooks = textbooks
            # Save the data that we've just changed to the underlying
            # MongoKeyValueStore before we update the mongo datastore.
            course_module.save()
            store.update_metadata(
                course_module.location,
                own_metadata(course_module)
            )
            return JsonResponse(course_module.pdf_textbooks)
    else:
        new_loc = loc_mapper().translate_location(location.course_id, location, False, True)
        upload_asset_url = new_loc.url_reverse('assets/', '')
        textbook_url = reverse('textbook_index', kwargs={
            'org': org,
            'course': course,
            'name': name,
        })
        return render_to_response('textbooks.html', {
            'context_course': course_module,
            'course': course_module,
            'upload_asset_url': upload_asset_url,
            'textbook_url': textbook_url,
        })


@require_POST
@login_required
@ensure_csrf_cookie
def create_textbook(request, org, course, name):
    """
    JSON API endpoint for creating a textbook. Used by the Backbone application.
    """
    location = get_location_and_verify_access(request, org, course, name)
    store = get_modulestore(location)
    course_module = store.get_item(location, depth=0)

    try:
        textbook = validate_textbook_json(request.body)
    except TextbookValidationError as err:
        return JsonResponse({"error": err.message}, status=400)
    if not textbook.get("id"):
        tids = set(t["id"] for t in course_module.pdf_textbooks if "id" in t)
        textbook["id"] = assign_textbook_id(textbook, tids)
    existing = course_module.pdf_textbooks
    existing.append(textbook)
    course_module.pdf_textbooks = existing
    if not any(tab['type'] == 'pdf_textbooks' for tab in course_module.tabs):
        tabs = course_module.tabs
        tabs.append({"type": "pdf_textbooks"})
        course_module.tabs = tabs
    # Save the data that we've just changed to the underlying
    # MongoKeyValueStore before we update the mongo datastore.
    course_module.save()
    store.update_metadata(course_module.location, own_metadata(course_module))
    resp = JsonResponse(textbook, status=201)
    resp["Location"] = reverse("textbook_by_id", kwargs={
        'org': org,
        'course': course,
        'name': name,
        'tid': textbook["id"],
    })
    return resp

def create_syllabus(request, org, course, name):
    """
    JSON API endpoint for creating a textbook. Used by the Backbone application.
    """
    pdb.set_trace()
    location = get_location_and_verify_access(request, org, course, name)
    store = get_modulestore(location)
    course_module = store.get_item(location, depth=0)

    try:
        syllabus = validate_syllabus_json(request.body)
    except SyllabusValidationError as err:
        return JsonResponse({"error": err.message}, status=400)
    if not syllabus.get("id"):
        tids = set(t["id"] for t in course_module.syllabus if "id" in t)
        syllabus["id"] = assign_syllabus_id(syllabus, tids)
    existing = course_module.syllabus
    existing.append(syllabus)
    if not any(tab['type'] == 'syllabus' for tab in course_module.tabs):
        tabs = course_module.tabs
        tabs.append({"type": "syllabus"})
        course_module.tabs = tabs
    # Save the data that we've just changed to the underlying
    # MongoKeyValueStore before we update the mongo datastore.
    course_module.save()
    store.update_metadata(course_module.location, own_metadata(course_module))
    resp = JsonResponse(syllabus, status=201)
    resp["Location"] = reverse("syllabus_by_id", kwargs={
        'org': org,
        'course': course,
        'name': name,
        'tid': syllabus["id"],
    })
    return resp    


@login_required
@ensure_csrf_cookie
@require_http_methods(("GET", "POST", "PUT", "DELETE"))
def textbook_by_id(request, org, course, name, tid):
    """
    JSON API endpoint for manipulating a textbook via its internal ID.
    Used by the Backbone application.
    """
    location = get_location_and_verify_access(request, org, course, name)
    store = get_modulestore(location)
    course_module = store.get_item(location, depth=3)
    matching_id = [tb for tb in course_module.pdf_textbooks
                   if str(tb.get("id")) == str(tid)]
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
        new_textbook["id"] = tid
        if textbook:
            i = course_module.pdf_textbooks.index(textbook)
            new_textbooks = course_module.pdf_textbooks[0:i]
            new_textbooks.append(new_textbook)
            new_textbooks.extend(course_module.pdf_textbooks[i + 1:])
            course_module.pdf_textbooks = new_textbooks
        else:
            course_module.pdf_textbooks.append(new_textbook)
        # Save the data that we've just changed to the underlying
        # MongoKeyValueStore before we update the mongo datastore.
        course_module.save()
        store.update_metadata(
            course_module.location,
            own_metadata(course_module)
        )
        return JsonResponse(new_textbook, status=201)
    elif request.method == 'DELETE':
        if not textbook:
            return JsonResponse(status=404)
        i = course_module.pdf_textbooks.index(textbook)
        new_textbooks = course_module.pdf_textbooks[0:i]
        new_textbooks.extend(course_module.pdf_textbooks[i + 1:])
        course_module.pdf_textbooks = new_textbooks
        course_module.save()
        store.update_metadata(
            course_module.location,
            own_metadata(course_module)
        )
        return JsonResponse()

@login_required
@ensure_csrf_cookie
@require_http_methods(("GET", "POST", "PUT", "DELETE"))
def syllabus_by_id(request, org, course, name, tid):
    """
    JSON API endpoint for manipulating a textbook via its internal ID.
    Used by the Backbone application.
    """
    location = get_location_and_verify_access(request, org, course, name)
    store = get_modulestore(location)
    course_module = store.get_item(location, depth=3)
    matching_id = [tb for tb in course_module.syllabus
                   if str(tb.get("id")) == str(tid)]
    if matching_id:
        topic = matching_id[0]
    else:
        topic = None

    if request.method == 'GET':
        if not topic:
            return JsonResponse(status=404)
        return JsonResponse(topic)
    elif request.method in ('POST', 'PUT'):  # can be either and sometimes
        pdb.set_trace()                                   # django is rewriting one to the other
        try:
            new_syllabus = validate_syllabus_json(request.body)
        except SyllabusValidationError as err:
            return JsonResponse({"error": err.message}, status=400)
        new_syllabus["id"] = tid
        if topic:
            i = course_module.syllabus.index(topic)
            new_syllabus = course_module.topic[0:i]
            new_syllabus.append(new_syllabus)
            new_syllabus.extend(course_module.syllabus[i + 1:])
            course_module.syllabus = new_syllabus
        else:
            course_module.syllabus.append(new_syllabus)
        # Save the data that we've just changed to the underlying
        # MongoKeyValueStore before we update the mongo datastore.
        course_module.save()
        store.update_metadata(
            course_module.location,
            own_metadata(course_module)
        )
        return JsonResponse(new_syllabus, status=201)
    elif request.method == 'DELETE':
        if not topic:
            return JsonResponse(status=404)
        i = course_module.syllabus.index(topic)
        new_syllabus = course_module.syllabus[0:i]
        new_syllabus.extend(course_module.syllabus[i + 1:])
        course_module.syllabus = new_syllabus
        course_module.save()
        store.update_metadata(
            course_module.location,
            own_metadata(course_module)
        )
        return JsonResponse()

def _get_course_creator_status(user):
    """
    Helper method for returning the course creator status for a particular user,
    taking into account the values of DISABLE_COURSE_CREATION and ENABLE_CREATOR_GROUP.

    If the user passed in has not previously visited the index page, it will be
    added with status 'unrequested' if the course creator group is in use.
    """
    if user.is_staff:
        course_creator_status = 'granted'
    elif settings.MITX_FEATURES.get('DISABLE_COURSE_CREATION', False):
        course_creator_status = 'disallowed_for_this_site'
    elif settings.MITX_FEATURES.get('ENABLE_CREATOR_GROUP', False):
        course_creator_status = get_course_creator_status(user)
        if course_creator_status is None:
            # User not grandfathered in as an existing user, has not previously visited the dashboard page.
            # Add the user to the course creator admin table with status 'unrequested'.
            add_user_with_status_unrequested(user)
            course_creator_status = get_course_creator_status(user)
    else:
        course_creator_status = 'granted'

    return course_creator_status
