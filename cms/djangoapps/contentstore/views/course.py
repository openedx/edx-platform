"""
Views related to operations on course objects
"""
import json

from django.contrib.auth.decorators import login_required
from django_future.csrf import ensure_csrf_cookie
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseBadRequest
from django.core.urlresolvers import reverse
from mitxmako.shortcuts import render_to_response

from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError, \
     InvalidLocationError
from xmodule.modulestore import Location

from contentstore.course_info_model import get_course_updates, update_course_updates, delete_course_update
from contentstore.utils import get_lms_link_for_item, add_extra_panel_tab, remove_extra_panel_tab
from models.settings.course_details import CourseDetails, CourseSettingsEncoder
from models.settings.course_grading import CourseGradingModel
from models.settings.course_metadata import CourseMetadata
from auth.authz import create_all_course_groups
from util.json_request import expect_json

from .access import has_access, get_location_and_verify_access
from .requests import get_request_method
from .tabs import initialize_course_tabs
from .component import OPEN_ENDED_COMPONENT_TYPES, \
     NOTE_COMPONENT_TYPES, ADVANCED_COMPONENT_POLICY_KEY

from django_comment_common.utils import seed_permissions_roles
import datetime
from django.utils.timezone import UTC
__all__ = ['course_index', 'create_new_course', 'course_info',
           'course_info_updates', 'get_course_settings',
           'course_config_graders_page',
           'course_config_advanced_page',
           'course_settings_updates',
           'course_grader_updates',
           'course_advanced_updates']


@login_required
@ensure_csrf_cookie
def course_index(request, org, course, name):
    """
    Display an editable course overview.

    org, course, name: Attributes of the Location for the item to edit
    """
    location = get_location_and_verify_access(request, org, course, name)

    lms_link = get_lms_link_for_item(location)

    upload_asset_callback_url = reverse('upload_asset', kwargs={
        'org': org,
        'course': course,
        'coursename': name
    })

    course = modulestore().get_item(location, depth=3)
    sections = course.get_children()

    return render_to_response('overview.html', {
        'active_tab': 'courseware',
        'context_course': course,
        'lms_link': lms_link,
        'sections': sections,
        'course_graders': json.dumps(CourseGradingModel.fetch(course.location).graders),
        'parent_location': course.location,
        'new_section_template': Location('i4x', 'edx', 'templates', 'chapter', 'Empty'),
        'new_subsection_template': Location('i4x', 'edx', 'templates', 'sequential', 'Empty'),  # for now they are the same, but the could be different at some point...
        'upload_asset_callback_url': upload_asset_callback_url,
        'create_new_unit_template': Location('i4x', 'edx', 'templates', 'vertical', 'Empty')
    })


@login_required
@expect_json
def create_new_course(request):

    if settings.MITX_FEATURES.get('DISABLE_COURSE_CREATION', False) and not request.user.is_staff:
        raise PermissionDenied()

    # This logic is repeated in xmodule/modulestore/tests/factories.py
    # so if you change anything here, you need to also change it there.
    # TODO: write a test that creates two courses, one with the factory and
    # the other with this method, then compare them to make sure they are
    # equivalent.
    template = Location(request.POST['template'])
    org = request.POST.get('org')
    number = request.POST.get('number')
    display_name = request.POST.get('display_name')

    try:
        dest_location = Location('i4x', org, number, 'course', Location.clean(display_name))
    except InvalidLocationError as error:
        return HttpResponse(json.dumps({'ErrMsg': "Unable to create course '" +
                                        display_name + "'.\n\n" + error.message}))

    # see if the course already exists
    existing_course = None
    try:
        existing_course = modulestore('direct').get_item(dest_location)
    except ItemNotFoundError:
        pass

    if existing_course is not None:
        return HttpResponse(json.dumps({'ErrMsg': 'There is already a course defined with this name.'}))

    course_search_location = ['i4x', dest_location.org, dest_location.course, 'course', None]
    courses = modulestore().get_items(course_search_location)

    if len(courses) > 0:
        return HttpResponse(json.dumps({'ErrMsg': 'There is already a course defined with the same organization and course number.'}))

    new_course = modulestore('direct').clone_item(template, dest_location)

    # clone a default 'about' module as well

    about_template_location = Location(['i4x', 'edx', 'templates', 'about', 'overview'])
    dest_about_location = dest_location._replace(category='about', name='overview')
    modulestore('direct').clone_item(about_template_location, dest_about_location)

    if display_name is not None:
        new_course.display_name = display_name

    # set a default start date to now
    new_course.start = datetime.datetime.now(UTC())

    initialize_course_tabs(new_course)

    create_all_course_groups(request.user, new_course.location)

    # seed the forums
    seed_permissions_roles(new_course.location.course_id)

    return HttpResponse(json.dumps({'id': new_course.location.url()}))


@login_required
@ensure_csrf_cookie
def course_info(request, org, course, name, provided_id=None):
    """
    Send models and views as well as html for editing the course info to the client.

    org, course, name: Attributes of the Location for the item to edit
    """
    location = get_location_and_verify_access(request, org, course, name)

    course_module = modulestore().get_item(location)

    # get current updates
    location = ['i4x', org, course, 'course_info', "updates"]

    return render_to_response('course_info.html', {
        'active_tab': 'courseinfo-tab',
        'context_course': course_module,
        'url_base': "/" + org + "/" + course + "/",
        'course_updates': json.dumps(get_course_updates(location)),
        'handouts_location': Location(['i4x', org, course, 'course_info', 'handouts']).url()
    })


@expect_json
@login_required
@ensure_csrf_cookie
def course_info_updates(request, org, course, provided_id=None):
    """
    restful CRUD operations on course_info updates.

    org, course: Attributes of the Location for the item to edit
    provided_id should be none if it's new (create) and a composite of the update db id + index otherwise.
    """
    # ??? No way to check for access permission afaik
    # get current updates
    location = ['i4x', org, course, 'course_info', "updates"]

    # Hmmm, provided_id is coming as empty string on create whereas I believe it used to be None :-(
    # Possibly due to my removing the seemingly redundant pattern in urls.py
    if provided_id == '':
        provided_id = None

    # check that logged in user has permissions to this item
    if not has_access(request.user, location):
        raise PermissionDenied()

    real_method = get_request_method(request)

    if request.method == 'GET':
        return HttpResponse(json.dumps(get_course_updates(location)),
                            mimetype="application/json")
    elif real_method == 'DELETE':
        try:
            return HttpResponse(json.dumps(delete_course_update(location,
                                request.POST, provided_id)), mimetype="application/json")
        except:
            return HttpResponseBadRequest("Failed to delete",
                                          content_type="text/plain")
    elif request.method == 'POST':
        try:
            return HttpResponse(json.dumps(update_course_updates(location,
                                request.POST, provided_id)), mimetype="application/json")
        except:
            return HttpResponseBadRequest("Failed to save",
                                          content_type="text/plain")


@login_required
@ensure_csrf_cookie
def get_course_settings(request, org, course, name):
    """
    Send models and views as well as html for editing the course settings to the client.

    org, course, name: Attributes of the Location for the item to edit
    """
    location = get_location_and_verify_access(request, org, course, name)

    course_module = modulestore().get_item(location)

    return render_to_response('settings.html', {
        'context_course': course_module,
        'course_location': location,
        'details_url': reverse(course_settings_updates,
                               kwargs={"org": org,
                                       "course": course,
                                       "name": name,
                                       "section": "details"}),
        'about_page_editable': not settings.MITX_FEATURES.get('ENABLE_MKTG_SITE', False)
    })


@login_required
@ensure_csrf_cookie
def course_config_graders_page(request, org, course, name):
    """
    Send models and views as well as html for editing the course settings to the client.

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
    Send models and views as well as html for editing the advanced course settings to the client.

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
    restful CRUD operations on course settings. This differs from get_course_settings by communicating purely
    through json (not rendering any html) and handles section level operations rather than whole page.

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
        return HttpResponse(json.dumps(manager.fetch(Location(['i4x', org, course, 'course', name])), cls=CourseSettingsEncoder),
                            mimetype="application/json")
    elif request.method == 'POST':  # post or put, doesn't matter.
        return HttpResponse(json.dumps(manager.update_from_json(request.POST), cls=CourseSettingsEncoder),
                            mimetype="application/json")


@expect_json
@login_required
@ensure_csrf_cookie
def course_grader_updates(request, org, course, name, grader_index=None):
    """
    restful CRUD operations on course_info updates. This differs from get_course_settings by communicating purely
    through json (not rendering any html) and handles section level operations rather than whole page.

    org, course: Attributes of the Location for the item to edit
    """

    location = get_location_and_verify_access(request, org, course, name)

    real_method = get_request_method(request)

    if real_method == 'GET':
        # Cannot just do a get w/o knowing the course name :-(
        return HttpResponse(json.dumps(CourseGradingModel.fetch_grader(Location(location), grader_index)),
                            mimetype="application/json")
    elif real_method == "DELETE":
        # ??? Should this return anything? Perhaps success fail?
        CourseGradingModel.delete_grader(Location(location), grader_index)
        return HttpResponse()
    elif request.method == 'POST':  # post or put, doesn't matter.
        return HttpResponse(json.dumps(CourseGradingModel.update_grader_from_json(Location(location), request.POST)),
                            mimetype="application/json")


# # NB: expect_json failed on ["key", "key2"] and json payload
@login_required
@ensure_csrf_cookie
def course_advanced_updates(request, org, course, name):
    """
    restful CRUD operations on metadata. The payload is a json rep of the metadata dicts. For delete, otoh,
    the payload is either a key or a list of keys to delete.

    org, course: Attributes of the Location for the item to edit
    """
    location = get_location_and_verify_access(request, org, course, name)

    real_method = get_request_method(request)

    if real_method == 'GET':
        return HttpResponse(json.dumps(CourseMetadata.fetch(location)),
                            mimetype="application/json")
    elif real_method == 'DELETE':
        return HttpResponse(json.dumps(CourseMetadata.delete_key(location,
                                                                 json.loads(request.body))),
                            mimetype="application/json")
    elif real_method == 'POST' or real_method == 'PUT':
        # NOTE: request.POST is messed up because expect_json
        # cloned_request.POST.copy() is creating a defective entry w/ the whole payload as the key
        request_body = json.loads(request.body)
        # Whether or not to filter the tabs key out of the settings metadata
        filter_tabs = True

        # Check to see if the user instantiated any advanced components. This is a hack
        # that does the following :
        #   1) adds/removes the open ended panel tab to a course automatically if the user
        #   has indicated that they want to edit the combinedopendended or peergrading module
        #   2) adds/removes the notes panel tab to a course automatically if the user has
        #   indicated that they want the notes module enabled in their course
        # TODO refactor the above into distinct advanced policy settings
        if ADVANCED_COMPONENT_POLICY_KEY in request_body:
            # Get the course so that we can scrape current tabs
            course_module = modulestore().get_item(location)

            # Maps tab types to components
            tab_component_map = {
                'open_ended': OPEN_ENDED_COMPONENT_TYPES,
                'notes': NOTE_COMPONENT_TYPES,
            }

            # Check to see if the user instantiated any notes or open ended components
            for tab_type in tab_component_map.keys():
                component_types = tab_component_map.get(tab_type)
                found_ac_type = False
                for ac_type in component_types:
                    if ac_type in request_body[ADVANCED_COMPONENT_POLICY_KEY]:
                        # Add tab to the course if needed
                        changed, new_tabs = add_extra_panel_tab(tab_type, course_module)
                        # If a tab has been added to the course, then send the metadata along to CourseMetadata.update_from_json
                        if changed:
                            course_module.tabs = new_tabs
                            request_body.update({'tabs': new_tabs})
                            # Indicate that tabs should not be filtered out of the metadata
                            filter_tabs = False
                        # Set this flag to avoid the tab removal code below.
                        found_ac_type = True
                        break
                # If we did not find a module type in the advanced settings,
                # we may need to remove the tab from the course.
                if not found_ac_type:
                    # Remove tab from the course if needed
                    changed, new_tabs = remove_extra_panel_tab(tab_type, course_module)
                    if changed:
                        course_module.tabs = new_tabs
                        request_body.update({'tabs': new_tabs})
                        # Indicate that tabs should *not* be filtered out of the metadata
                        filter_tabs = False
        try:
            response_json = json.dumps(CourseMetadata.update_from_json(location,
                                                                   request_body,
                                                                   filter_tabs=filter_tabs))
        except (TypeError, ValueError), e:
            return HttpResponseBadRequest("Incorrect setting format. " + str(e), content_type="text/plain")

        return HttpResponse(response_json, mimetype="application/json")
