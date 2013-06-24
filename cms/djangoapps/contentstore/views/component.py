import json
import logging
from collections import defaultdict

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django_future.csrf import ensure_csrf_cookie
from django.conf import settings
from xmodule.modulestore.exceptions import ItemNotFoundError, InvalidLocationError
from mitxmako.shortcuts import render_to_response

from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.util.date_utils import get_default_time_display

from xblock.core import Scope
from util.json_request import expect_json

from contentstore.module_info_model import get_module_info, set_module_info
from contentstore.utils import get_modulestore, get_lms_link_for_item, \
    compute_unit_state, UnitState, get_course_for_item

from models.settings.course_grading import CourseGradingModel

from .requests import get_request_method, _xmodule_recurse
from .access import has_access

__all__ = ['OPEN_ENDED_COMPONENT_TYPES',
           'ADVANCED_COMPONENT_POLICY_KEY',
           'edit_subsection',
           'edit_unit',
           'assignment_type_update',
           'create_draft',
           'publish_draft',
           'unpublish_unit',
           'module_info']

log = logging.getLogger(__name__)

COMPONENT_TYPES = ['customtag', 'discussion', 'html', 'problem', 'video']

OPEN_ENDED_COMPONENT_TYPES = ["combinedopenended", "peergrading"]
NOTE_COMPONENT_TYPES = ['notes']
ADVANCED_COMPONENT_TYPES = ['annotatable', 'word_cloud', 'videoalpha'] + OPEN_ENDED_COMPONENT_TYPES + NOTE_COMPONENT_TYPES
ADVANCED_COMPONENT_CATEGORY = 'advanced'
ADVANCED_COMPONENT_POLICY_KEY = 'advanced_modules'


@login_required
def edit_subsection(request, location):
    # check that we have permissions to edit this item
    try:
        course = get_course_for_item(location)
    except InvalidLocationError:
        return HttpResponseBadRequest()

    if not has_access(request.user, course.location):
        raise PermissionDenied()

    try:
        item = modulestore().get_item(location, depth=1)
    except ItemNotFoundError:
        return HttpResponseBadRequest()

    lms_link = get_lms_link_for_item(location, course_id=course.location.course_id)
    preview_link = get_lms_link_for_item(location, course_id=course.location.course_id, preview=True)

    # make sure that location references a 'sequential', otherwise return BadRequest
    if item.location.category != 'sequential':
        return HttpResponseBadRequest()

    parent_locs = modulestore().get_parent_locations(location, None)

    # we're for now assuming a single parent
    if len(parent_locs) != 1:
        logging.error('Multiple (or none) parents have been found for {0}'.format(location))

    # this should blow up if we don't find any parents, which would be erroneous
    parent = modulestore().get_item(parent_locs[0])

    # remove all metadata from the generic dictionary that is presented in a more normalized UI

    policy_metadata = dict(
        (field.name, field.read_from(item))
        for field
        in item.fields
        if field.name not in ['display_name', 'start', 'due', 'format'] and field.scope == Scope.settings
    )

    can_view_live = False
    subsection_units = item.get_children()
    for unit in subsection_units:
        state = compute_unit_state(unit)
        if state == UnitState.public or state == UnitState.draft:
            can_view_live = True
            break

    return render_to_response('edit_subsection.html',
                              {'subsection': item,
                               'context_course': course,
                               'create_new_unit_template': Location('i4x', 'edx', 'templates', 'vertical', 'Empty'),
                               'lms_link': lms_link,
                               'preview_link': preview_link,
                               'course_graders': json.dumps(CourseGradingModel.fetch(course.location).graders),
                               'parent_location': course.location,
                               'parent_item': parent,
                               'policy_metadata': policy_metadata,
                               'subsection_units': subsection_units,
                               'can_view_live': can_view_live
                               })


@login_required
def edit_unit(request, location):
    """
    Display an editing page for the specified module.

    Expects a GET request with the parameter 'id'.

    id: A Location URL
    """
    try:
        course = get_course_for_item(location)
    except InvalidLocationError:
        return HttpResponseBadRequest()

    if not has_access(request.user, course.location):
        raise PermissionDenied()

    try:
        item = modulestore().get_item(location, depth=1)
    except ItemNotFoundError:
        return HttpResponseBadRequest()

    lms_link = get_lms_link_for_item(item.location, course_id=course.location.course_id)

    component_templates = defaultdict(list)

    # Check if there are any advanced modules specified in the course policy. These modules
    # should be specified as a list of strings, where the strings are the names of the modules
    # in ADVANCED_COMPONENT_TYPES that should be enabled for the course.
    course_advanced_keys = course.advanced_modules

    # Set component types according to course policy file
    component_types = list(COMPONENT_TYPES)
    if isinstance(course_advanced_keys, list):
        course_advanced_keys = [c for c in course_advanced_keys if c in ADVANCED_COMPONENT_TYPES]
        if len(course_advanced_keys) > 0:
            component_types.append(ADVANCED_COMPONENT_CATEGORY)
    else:
        log.error("Improper format for course advanced keys! {0}".format(course_advanced_keys))

    templates = modulestore().get_items(Location('i4x', 'edx', 'templates'))
    for template in templates:
        category = template.location.category

        if category in course_advanced_keys:
            category = ADVANCED_COMPONENT_CATEGORY

        if category in component_types:
            # This is a hack to create categories for different xmodules
            component_templates[category].append((
                template.display_name_with_default,
                template.location.url(),
                hasattr(template, 'markdown') and template.markdown is not None
            ))

    components = [
        component.location.url()
        for component
        in item.get_children()
    ]

    # TODO (cpennington): If we share units between courses,
    # this will need to change to check permissions correctly so as
    # to pick the correct parent subsection

    containing_subsection_locs = modulestore().get_parent_locations(location, None)
    containing_subsection = modulestore().get_item(containing_subsection_locs[0])

    containing_section_locs = modulestore().get_parent_locations(containing_subsection.location, None)
    containing_section = modulestore().get_item(containing_section_locs[0])

    # cdodge hack. We're having trouble previewing drafts via jump_to redirect
    # so let's generate the link url here

    # need to figure out where this item is in the list of children as the preview will need this
    index = 1
    for child in containing_subsection.get_children():
        if child.location == item.location:
            break
        index = index + 1

    preview_lms_base = settings.MITX_FEATURES.get('PREVIEW_LMS_BASE')

    preview_lms_link = '//{preview_lms_base}/courses/{org}/{course}/{course_name}/courseware/{section}/{subsection}/{index}'.format(
        preview_lms_base=preview_lms_base,
        lms_base=settings.LMS_BASE,
        org=course.location.org,
        course=course.location.course,
        course_name=course.location.name,
        section=containing_section.location.name,
        subsection=containing_subsection.location.name,
        index=index)

    unit_state = compute_unit_state(item)

    return render_to_response('unit.html', {
        'context_course': course,
        'active_tab': 'courseware',
        'unit': item,
        'unit_location': location,
        'components': components,
        'component_templates': component_templates,
        'draft_preview_link': preview_lms_link,
        'published_preview_link': lms_link,
        'subsection': containing_subsection,
        'release_date': get_default_time_display(containing_subsection.lms.start) if containing_subsection.lms.start is not None else None,
        'section': containing_section,
        'create_new_unit_template': Location('i4x', 'edx', 'templates', 'vertical', 'Empty'),
        'unit_state': unit_state,
        'published_date': item.cms.published_date.strftime('%B %d, %Y') if item.cms.published_date is not None else None,
    })


@expect_json
@login_required
@ensure_csrf_cookie
def assignment_type_update(request, org, course, category, name):
    '''
    CRUD operations on assignment types for sections and subsections and anything else gradable.
    '''
    location = Location(['i4x', org, course, category, name])
    if not has_access(request.user, location):
        raise HttpResponseForbidden()

    if request.method == 'GET':
        return HttpResponse(json.dumps(CourseGradingModel.get_section_grader_type(location)),
                            mimetype="application/json")
    elif request.method == 'POST':  # post or put, doesn't matter.
        return HttpResponse(json.dumps(CourseGradingModel.update_section_grader_type(location, request.POST)),
                            mimetype="application/json")


@login_required
@expect_json
def create_draft(request):
    location = request.POST['id']

    # check permissions for this user within this course
    if not has_access(request.user, location):
        raise PermissionDenied()

    # This clones the existing item location to a draft location (the draft is implicit,
    # because modulestore is a Draft modulestore)
    modulestore().clone_item(location, location)

    return HttpResponse()


@login_required
@expect_json
def publish_draft(request):
    location = request.POST['id']

    # check permissions for this user within this course
    if not has_access(request.user, location):
        raise PermissionDenied()

    item = modulestore().get_item(location)
    _xmodule_recurse(item, lambda i: modulestore().publish(i.location, request.user.id))

    return HttpResponse()


@login_required
@expect_json
def unpublish_unit(request):
    location = request.POST['id']

    # check permissions for this user within this course
    if not has_access(request.user, location):
        raise PermissionDenied()

    item = modulestore().get_item(location)
    _xmodule_recurse(item, lambda i: modulestore().unpublish(i.location))

    return HttpResponse()


@expect_json
@login_required
@ensure_csrf_cookie
def module_info(request, module_location):
    location = Location(module_location)

    # check that logged in user has permissions to this item
    if not has_access(request.user, location):
        raise PermissionDenied()

    real_method = get_request_method(request)

    rewrite_static_links = request.GET.get('rewrite_url_links', 'True') in ['True', 'true']
    logging.debug('rewrite_static_links = {0} {1}'.format(request.GET.get('rewrite_url_links', 'False'), rewrite_static_links))

    # check that logged in user has permissions to this item
    if not has_access(request.user, location):
        raise PermissionDenied()

    if real_method == 'GET':
        return HttpResponse(json.dumps(get_module_info(get_modulestore(location), location, rewrite_static_links=rewrite_static_links)), mimetype="application/json")
    elif real_method == 'POST' or real_method == 'PUT':
        return HttpResponse(json.dumps(set_module_info(get_modulestore(location), location, request.POST)), mimetype="application/json")
    else:
        return HttpResponseBadRequest()
