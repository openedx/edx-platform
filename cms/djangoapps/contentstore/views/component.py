import json
import logging
from collections import defaultdict

from django.http import (HttpResponse, HttpResponseBadRequest,
        HttpResponseForbidden)
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from django_future.csrf import ensure_csrf_cookie
from django.conf import settings
from xmodule.modulestore.exceptions import (ItemNotFoundError,
        InvalidLocationError)
from mitxmako.shortcuts import render_to_response

from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.util.date_utils import get_default_time_display

from xblock.fields import Scope
from util.json_request import expect_json, JsonResponse

from contentstore.module_info_model import get_module_info, set_module_info
from contentstore.utils import (get_modulestore, get_lms_link_for_item,
    compute_unit_state, UnitState, get_course_for_item)

from models.settings.course_grading import CourseGradingModel

from .helpers import _xmodule_recurse
from .access import has_access
from xmodule.x_module import XModuleDescriptor
from xblock.plugin import PluginMissingError
from xblock.runtime import Mixologist

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

# NOTE: edit_unit assumes this list is disjoint from ADVANCED_COMPONENT_TYPES
COMPONENT_TYPES = ['discussion', 'html', 'problem', 'video']

OPEN_ENDED_COMPONENT_TYPES = ["combinedopenended", "peergrading"]
NOTE_COMPONENT_TYPES = ['notes']
ADVANCED_COMPONENT_TYPES = [
    'annotatable',
    'word_cloud',
    'graphical_slider_tool',
    'lti',
] + OPEN_ENDED_COMPONENT_TYPES + NOTE_COMPONENT_TYPES
ADVANCED_COMPONENT_CATEGORY = 'advanced'
ADVANCED_COMPONENT_POLICY_KEY = 'advanced_modules'


@login_required
def edit_subsection(request, location):
    "Edit the subsection of a course"
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

    lms_link = get_lms_link_for_item(
            location, course_id=course.location.course_id
    )
    preview_link = get_lms_link_for_item(
            location, course_id=course.location.course_id, preview=True
    )

    # make sure that location references a 'sequential', otherwise return
    # BadRequest
    if item.location.category != 'sequential':
        return HttpResponseBadRequest()

    parent_locs = modulestore().get_parent_locations(location, None)

    # we're for now assuming a single parent
    if len(parent_locs) != 1:
        logging.error(
                'Multiple (or none) parents have been found for %s',
                location
        )

    # this should blow up if we don't find any parents, which would be erroneous
    parent = modulestore().get_item(parent_locs[0])

    # remove all metadata from the generic dictionary that is presented in a
    # more normalized UI. We only want to display the XBlocks fields, not
    # the fields from any mixins that have been added
    fields = getattr(item, 'unmixed_class', item.__class__).fields

    policy_metadata = dict(
        (field.name, field.read_from(item))
        for field
        in fields.values()
        if field.name not in ['display_name', 'start', 'due', 'format']
            and field.scope == Scope.settings
    )

    can_view_live = False
    subsection_units = item.get_children()
    for unit in subsection_units:
        state = compute_unit_state(unit)
        if state == UnitState.public or state == UnitState.draft:
            can_view_live = True
            break

    return render_to_response(
        'edit_subsection.html',
        {
           'subsection': item,
           'context_course': course,
           'new_unit_category': 'vertical',
           'lms_link': lms_link,
           'preview_link': preview_link,
           'course_graders': json.dumps(CourseGradingModel.fetch(course.location).graders),
           'parent_location': course.location,
           'parent_item': parent,
           'policy_metadata': policy_metadata,
           'subsection_units': subsection_units,
           'can_view_live': can_view_live
        }
    )


def load_mixed_class(category):
    """
    Load an XBlock by category name, and apply all defined mixins
    """
    component_class = XModuleDescriptor.load_class(category)
    mixologist = Mixologist(settings.XBLOCK_MIXINS)
    return mixologist.mix(component_class)


@login_required
def edit_unit(request, location):
    """
    Display an editing page for the specified module.

    Expects a GET request with the parameter `id`.

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
    lms_link = get_lms_link_for_item(
            item.location,
            course_id=course.location.course_id
    )

    component_templates = defaultdict(list)
    for category in COMPONENT_TYPES:
        component_class = load_mixed_class(category)
        # add the default template
        # TODO: Once mixins are defined per-application, rather than per-runtime,
        # this should use a cms mixed-in class. (cpennington)
        if hasattr(component_class, 'display_name'):
            display_name = component_class.display_name.default or 'Blank'
        else:
            display_name = 'Blank'
        component_templates[category].append((
            display_name,
            category,
            False,  # No defaults have markdown (hardcoded current default)
            None  # no boilerplate for overrides
        ))
        # add boilerplates
        if hasattr(component_class, 'templates'):
            for template in component_class.templates():
                component_templates[category].append((
                    template['metadata'].get('display_name'),
                    category,
                    template['metadata'].get('markdown') is not None,
                    template.get('template_id')
                ))

    # Check if there are any advanced modules specified in the course policy.
    # These modules should be specified as a list of strings, where the strings
    # are the names of the modules in ADVANCED_COMPONENT_TYPES that should be
    # enabled for the course.
    course_advanced_keys = course.advanced_modules

    # Set component types according to course policy file
    if isinstance(course_advanced_keys, list):
        for category in course_advanced_keys:
            if category in ADVANCED_COMPONENT_TYPES:
                # Do I need to allow for boilerplates or just defaults on the
                # class? i.e., can an advanced have more than one entry in the
                # menu? one for default and others for prefilled boilerplates?
                try:
                    component_class = load_mixed_class(category)

                    component_templates['advanced'].append((
                        component_class.display_name.default or category,
                        category,
                        False,
                        None  # don't override default data
                        ))
                except PluginMissingError:
                    # dhm: I got this once but it can happen any time the
                    # course author configures an advanced component which does
                    # not exist on the server. This code here merely
                    # prevents any authors from trying to instantiate the
                    # non-existent component type by not showing it in the menu
                    pass
    else:
        log.error(
            "Improper format for course advanced keys! %",
            course_advanced_keys
        )

    components = [
        component.location.url()
        for component
        in item.get_children()
    ]

    # TODO (cpennington): If we share units between courses,
    # this will need to change to check permissions correctly so as
    # to pick the correct parent subsection

    containing_subsection_locs = modulestore().get_parent_locations(
            location, None
    )
    containing_subsection = modulestore().get_item(containing_subsection_locs[0])
    containing_section_locs = modulestore().get_parent_locations(
            containing_subsection.location, None
    )
    containing_section = modulestore().get_item(containing_section_locs[0])

    # cdodge hack. We're having trouble previewing drafts via jump_to redirect
    # so let's generate the link url here

    # need to figure out where this item is in the list of children as the
    # preview will need this
    index = 1
    for child in containing_subsection.get_children():
        if child.location == item.location:
            break
        index = index + 1

    preview_lms_base = settings.MITX_FEATURES.get('PREVIEW_LMS_BASE')

    preview_lms_link = (
            '//{preview_lms_base}/courses/{org}/{course}/'
            '{course_name}/courseware/{section}/{subsection}/{index}'
        ).format(
            preview_lms_base=preview_lms_base,
            lms_base=settings.LMS_BASE,
            org=course.location.org,
            course=course.location.course,
            course_name=course.location.name,
            section=containing_section.location.name,
            subsection=containing_subsection.location.name,
            index=index
        )

    unit_state = compute_unit_state(item)

    return render_to_response('unit.html', {
        'context_course': course,
        'unit': item,
        'unit_location': location,
        'components': components,
        'component_templates': component_templates,
        'draft_preview_link': preview_lms_link,
        'published_preview_link': lms_link,
        'subsection': containing_subsection,
        'release_date': (
            get_default_time_display(containing_subsection.start)
            if containing_subsection.start is not None else None
        ),
        'section': containing_section,
        'new_unit_category': 'vertical',
        'unit_state': unit_state,
        'published_date': (
            get_default_time_display(item.published_date)
            if item.published_date is not None else None
        ),
    })


@expect_json
@login_required
@require_http_methods(("GET", "POST", "PUT"))
@ensure_csrf_cookie
def assignment_type_update(request, org, course, category, name):
    """
    CRUD operations on assignment types for sections and subsections and
    anything else gradable.
    """
    location = Location(['i4x', org, course, category, name])
    if not has_access(request.user, location):
        return HttpResponseForbidden()

    if request.method == 'GET':
        rsp = CourseGradingModel.get_section_grader_type(location)
    elif request.method in ('POST', 'PUT'):  # post or put, doesn't matter.
        rsp = CourseGradingModel.update_section_grader_type(
                    location, request.POST
        )
    return JsonResponse(rsp)


@login_required
@expect_json
def create_draft(request):
    "Create a draft"
    location = request.POST['id']

    # check permissions for this user within this course
    if not has_access(request.user, location):
        raise PermissionDenied()

    # This clones the existing item location to a draft location (the draft is
    # implicit, because modulestore is a Draft modulestore)
    modulestore().convert_to_draft(location)

    return HttpResponse()


@login_required
@expect_json
def publish_draft(request):
    """
    Publish a draft
    """
    location = request.POST['id']

    # check permissions for this user within this course
    if not has_access(request.user, location):
        raise PermissionDenied()

    item = modulestore().get_item(location)
    _xmodule_recurse(
            item,
            lambda i: modulestore().publish(i.location, request.user.id)
    )

    return HttpResponse()


@login_required
@expect_json
def unpublish_unit(request):
    "Unpublish a unit"
    location = request.POST['id']

    # check permissions for this user within this course
    if not has_access(request.user, location):
        raise PermissionDenied()

    item = modulestore().get_item(location)
    _xmodule_recurse(item, lambda i: modulestore().unpublish(i.location))

    return HttpResponse()


@expect_json
@require_http_methods(("GET", "POST", "PUT"))
@login_required
@ensure_csrf_cookie
def module_info(request, module_location):
    "Get or set information for a module in the modulestore"
    location = Location(module_location)

    # check that logged in user has permissions to this item
    if not has_access(request.user, location):
        raise PermissionDenied()

    rewrite_static_links = request.GET.get('rewrite_url_links', 'True') in ['True', 'true']
    logging.debug('rewrite_static_links = {0} {1}'.format(
        request.GET.get('rewrite_url_links', False),
        rewrite_static_links)
    )

    # check that logged in user has permissions to this item
    if not has_access(request.user, location):
        raise PermissionDenied()

    if request.method == 'GET':
        rsp = get_module_info(
            get_modulestore(location),
            location,
            rewrite_static_links=rewrite_static_links
        )
    elif request.method in ("POST", "PUT"):
        rsp = set_module_info(
            get_modulestore(location),
            location, request.POST
        )
    return JsonResponse(rsp)
