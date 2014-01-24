import json
import logging
from collections import defaultdict

from django.http import HttpResponseBadRequest, Http404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from django.conf import settings
from xmodule.modulestore.exceptions import ItemNotFoundError
from edxmako.shortcuts import render_to_response

from xmodule.modulestore.django import modulestore
from xmodule.util.date_utils import get_default_time_display
from xmodule.modulestore.django import loc_mapper
from xmodule.modulestore.locator import BlockUsageLocator

from xblock.core import XBlock
from xblock.django.request import webob_to_django_response, django_to_webob_request
from xblock.exceptions import NoSuchHandlerError
from xblock.fields import Scope
from xblock.plugin import PluginMissingError
from xblock.runtime import Mixologist
from xmodule.x_module import prefer_xmodules

from lms.lib.xblock.runtime import unquote_slashes

from contentstore.utils import get_lms_link_for_item, compute_unit_state, UnitState

from models.settings.course_grading import CourseGradingModel

from .access import has_course_access

__all__ = ['OPEN_ENDED_COMPONENT_TYPES',
           'ADVANCED_COMPONENT_POLICY_KEY',
           'subsection_handler',
           'unit_handler',
           'component_handler'
           ]

log = logging.getLogger(__name__)

# NOTE: unit_handler assumes this list is disjoint from ADVANCED_COMPONENT_TYPES
COMPONENT_TYPES = ['discussion', 'html', 'problem', 'video']

OPEN_ENDED_COMPONENT_TYPES = ["combinedopenended", "peergrading"]
NOTE_COMPONENT_TYPES = ['notes']

if settings.FEATURES.get('ALLOW_ALL_ADVANCED_COMPONENTS'):
    ADVANCED_COMPONENT_TYPES = sorted(set(name for name, class_ in XBlock.load_classes()) - set(COMPONENT_TYPES))
else:

    ADVANCED_COMPONENT_TYPES = [
        'annotatable',
        'word_cloud',
        'graphical_slider_tool',
        'lti',
    ] + OPEN_ENDED_COMPONENT_TYPES + NOTE_COMPONENT_TYPES

ADVANCED_COMPONENT_CATEGORY = 'advanced'
ADVANCED_COMPONENT_POLICY_KEY = 'advanced_modules'


@require_http_methods(["GET"])
@login_required
def subsection_handler(request, tag=None, package_id=None, branch=None, version_guid=None, block=None):
    """
    The restful handler for subsection-specific requests.

    GET
        html: return html page for editing a subsection
        json: not currently supported
    """
    if 'text/html' in request.META.get('HTTP_ACCEPT', 'text/html'):
        locator = BlockUsageLocator(package_id=package_id, branch=branch, version_guid=version_guid, block_id=block)
        try:
            old_location, course, item, lms_link = _get_item_in_course(request, locator)
        except ItemNotFoundError:
            return HttpResponseBadRequest()

        preview_link = get_lms_link_for_item(old_location, course_id=course.location.course_id, preview=True)

        # make sure that location references a 'sequential', otherwise return
        # BadRequest
        if item.location.category != 'sequential':
            return HttpResponseBadRequest()

        parent_locs = modulestore().get_parent_locations(old_location, None)

        # we're for now assuming a single parent
        if len(parent_locs) != 1:
            logging.error(
                'Multiple (or none) parents have been found for %s',
                unicode(locator)
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
            if field.name not in ['display_name', 'start', 'due', 'format'] and field.scope == Scope.settings
        )

        can_view_live = False
        subsection_units = item.get_children()
        for unit in subsection_units:
            state = compute_unit_state(unit)
            if state == UnitState.public or state == UnitState.draft:
                can_view_live = True
                break

        course_locator = loc_mapper().translate_location(
            course.location.course_id, course.location, False, True
        )

        return render_to_response(
            'edit_subsection.html',
            {
                'subsection': item,
                'context_course': course,
                'new_unit_category': 'vertical',
                'lms_link': lms_link,
                'preview_link': preview_link,
                'course_graders': json.dumps(CourseGradingModel.fetch(course_locator).graders),
                'parent_item': parent,
                'locator': locator,
                'policy_metadata': policy_metadata,
                'subsection_units': subsection_units,
                'can_view_live': can_view_live
            }
        )
    else:
        return HttpResponseBadRequest("Only supports html requests")


def _load_mixed_class(category):
    """
    Load an XBlock by category name, and apply all defined mixins
    """
    component_class = XBlock.load_class(category, select=prefer_xmodules)
    mixologist = Mixologist(settings.XBLOCK_MIXINS)
    return mixologist.mix(component_class)


@require_http_methods(["GET"])
@login_required
def unit_handler(request, tag=None, package_id=None, branch=None, version_guid=None, block=None):
    """
    The restful handler for unit-specific requests.

    GET
        html: return html page for editing a unit
        json: not currently supported
    """
    if 'text/html' in request.META.get('HTTP_ACCEPT', 'text/html'):
        locator = BlockUsageLocator(package_id=package_id, branch=branch, version_guid=version_guid, block_id=block)
        try:
            old_location, course, item, lms_link = _get_item_in_course(request, locator)
        except ItemNotFoundError:
            return HttpResponseBadRequest()

        component_templates = defaultdict(list)
        for category in COMPONENT_TYPES:
            component_class = _load_mixed_class(category)
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
                    filter_templates = getattr(component_class, 'filter_templates', None)
                    if not filter_templates or filter_templates(template, course):
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
                        component_class = _load_mixed_class(category)

                        component_templates['advanced'].append(
                            (
                                component_class.display_name.default or category,
                                category,
                                False,
                                None  # don't override default data
                            )
                        )
                    except PluginMissingError:
                        # dhm: I got this once but it can happen any time the
                        # course author configures an advanced component which does
                        # not exist on the server. This code here merely
                        # prevents any authors from trying to instantiate the
                        # non-existent component type by not showing it in the menu
                        pass
        else:
            log.error(
                "Improper format for course advanced keys! %s",
                course_advanced_keys
            )

        components = [
            loc_mapper().translate_location(
                course.location.course_id, component.location, False, True
            )
            for component
            in item.get_children()
        ]

        # TODO (cpennington): If we share units between courses,
        # this will need to change to check permissions correctly so as
        # to pick the correct parent subsection

        containing_subsection_locs = modulestore().get_parent_locations(old_location, None)
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

        preview_lms_base = settings.FEATURES.get('PREVIEW_LMS_BASE')

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

        return render_to_response('unit.html', {
            'context_course': course,
            'unit': item,
            'unit_locator': locator,
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
            'unit_state': compute_unit_state(item),
            'published_date': (
                get_default_time_display(item.published_date)
                if item.published_date is not None else None
            ),
        })
    else:
        return HttpResponseBadRequest("Only supports html requests")


@login_required
def _get_item_in_course(request, locator):
    """
    Helper method for getting the old location, containing course,
    item, and lms_link for a given locator.

    Verifies that the caller has permission to access this item.
    """
    if not has_course_access(request.user, locator):
        raise PermissionDenied()

    old_location = loc_mapper().translate_locator_to_location(locator)
    course_location = loc_mapper().translate_locator_to_location(locator, True)
    course = modulestore().get_item(course_location)
    item = modulestore().get_item(old_location, depth=1)
    lms_link = get_lms_link_for_item(old_location, course_id=course.location.course_id)

    return old_location, course, item, lms_link


@login_required
def component_handler(request, usage_id, handler, suffix=''):
    """
    Dispatch an AJAX action to an xblock

    Args:
        usage_id: The usage-id of the block to dispatch to, passed through `quote_slashes`
        handler (str): The handler to execute
        suffix (str): The remainder of the url to be passed to the handler

    Returns:
        :class:`django.http.HttpResponse`: The response from the handler, converted to a
            django response
    """

    location = unquote_slashes(usage_id)

    descriptor = modulestore().get_item(location)
    # Let the module handle the AJAX
    req = django_to_webob_request(request)

    try:
        resp = descriptor.handle(handler, req, suffix)

    except NoSuchHandlerError:
        log.info("XBlock %s attempted to access missing handler %r", descriptor, handler, exc_info=True)
        raise Http404

    modulestore().save_xmodule(descriptor)

    return webob_to_django_response(resp)
