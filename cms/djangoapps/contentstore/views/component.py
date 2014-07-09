from __future__ import absolute_import

import json
import logging

from django.http import HttpResponseBadRequest, Http404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.core.exceptions import PermissionDenied
from django.conf import settings
from xmodule.modulestore.exceptions import ItemNotFoundError
from edxmako.shortcuts import render_to_response

from util.date_utils import get_default_time_display
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import PublishState

from xblock.core import XBlock
from xblock.django.request import webob_to_django_response, django_to_webob_request
from xblock.exceptions import NoSuchHandlerError
from xblock.fields import Scope
from xblock.plugin import PluginMissingError
from xblock.runtime import Mixologist

from contentstore.utils import get_lms_link_for_item, compute_publish_state
from contentstore.views.helpers import get_parent_xblock

from models.settings.course_grading import CourseGradingModel
from opaque_keys.edx.keys import UsageKey

from .access import has_course_access
from django.utils.translation import ugettext as _

__all__ = ['OPEN_ENDED_COMPONENT_TYPES',
           'ADVANCED_COMPONENT_POLICY_KEY',
           'subsection_handler',
           'unit_handler',
           'container_handler',
           'component_handler'
           ]

log = logging.getLogger(__name__)

# NOTE: unit_handler assumes this list is disjoint from ADVANCED_COMPONENT_TYPES
COMPONENT_TYPES = ['discussion', 'html', 'problem', 'video']
SPLIT_TEST_COMPONENT_TYPE = 'split_test'

OPEN_ENDED_COMPONENT_TYPES = ["combinedopenended", "peergrading"]
NOTE_COMPONENT_TYPES = ['notes']
if settings.FEATURES.get('ALLOW_ALL_ADVANCED_COMPONENTS'):
    ADVANCED_COMPONENT_TYPES = sorted(set(name for name, class_ in XBlock.load_classes()) - set(COMPONENT_TYPES))
else:

    ADVANCED_COMPONENT_TYPES = [
        'annotatable',
        'textannotation',  # module for annotating text (with annotation table)
        'videoannotation',  # module for annotating video (with annotation table)
        'imageannotation',  # module for annotating image (with annotation table)
        'word_cloud',
        'graphical_slider_tool',
        'lti',
        # XBlocks from pmitros repos are prototypes. They should not be used
        # except for edX Learning Sciences experiments on edge.edx.org without
        # further work to make them robust, maintainable, finalize data formats,
        # etc.
        'concept',  # Concept mapper. See https://github.com/pmitros/ConceptXBlock
        'done',  # Lets students mark things as done. See https://github.com/pmitros/DoneXBlock
        'audio',  # Embed an audio file. See https://github.com/pmitros/AudioXBlock
        SPLIT_TEST_COMPONENT_TYPE,  # Adds A/B test support
    ] + OPEN_ENDED_COMPONENT_TYPES + NOTE_COMPONENT_TYPES

ADVANCED_COMPONENT_CATEGORY = 'advanced'
ADVANCED_COMPONENT_POLICY_KEY = 'advanced_modules'

# Specify xblocks that should be treated as advanced problems. Each entry is a tuple
# specifying the xblock name and an optional YAML template to be used.
ADVANCED_PROBLEM_TYPES = [
    {
        'component': 'openassessment',
        'boilerplate_name': None
    }
]

@require_GET
@login_required
def subsection_handler(request, usage_key_string):
    """
    The restful handler for subsection-specific requests.

    GET
        html: return html page for editing a subsection
        json: not currently supported
    """
    if 'text/html' in request.META.get('HTTP_ACCEPT', 'text/html'):
        usage_key = UsageKey.from_string(usage_key_string)
        try:
            course, item, lms_link = _get_item_in_course(request, usage_key)
        except ItemNotFoundError:
            return HttpResponseBadRequest()

        preview_link = get_lms_link_for_item(item.location, preview=True)

        # make sure that location references a 'sequential', otherwise return
        # BadRequest
        if item.location.category != 'sequential':
            return HttpResponseBadRequest()

        parent = get_parent_xblock(item)

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
            state = compute_publish_state(unit)
            if state in (PublishState.public, PublishState.draft):
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
                'course_graders': json.dumps(CourseGradingModel.fetch(item.location.course_key).graders),
                'parent_item': parent,
                'locator': item.location,
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
    component_class = XBlock.load_class(category, select=settings.XBLOCK_SELECT_FUNCTION)
    mixologist = Mixologist(settings.XBLOCK_MIXINS)
    return mixologist.mix(component_class)


@require_GET
@login_required
def unit_handler(request, usage_key_string):
    """
    The restful handler for unit-specific requests.

    GET
        html: return html page for editing a unit
        json: not currently supported
    """
    if 'text/html' in request.META.get('HTTP_ACCEPT', 'text/html'):
        usage_key = UsageKey.from_string(usage_key_string)
        try:
            course, item, lms_link = _get_item_in_course(request, usage_key)
        except ItemNotFoundError:
            return HttpResponseBadRequest()

        component_templates = get_component_templates(course)

        xblocks = item.get_children()

        # TODO (cpennington): If we share units between courses,
        # this will need to change to check permissions correctly so as
        # to pick the correct parent subsection
        containing_subsection = get_parent_xblock(item)
        containing_section = get_parent_xblock(containing_subsection)

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
            u'//{preview_lms_base}/courses/{org}/{course}/{course_name}/courseware/{section}/{subsection}/{index}'
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
            'unit_usage_key': item.location,
            'child_usage_keys': [block.scope_ids.usage_id for block in xblocks],
            'component_templates': json.dumps(component_templates),
            'draft_preview_link': preview_lms_link,
            'published_preview_link': lms_link,
            'subsection': containing_subsection,
            'release_date': (
                get_default_time_display(containing_subsection.start)
                if containing_subsection.start is not None else None
            ),
            'section': containing_section,
            'new_unit_category': 'vertical',
            'unit_state': compute_publish_state(item),
            'published_date': (
                get_default_time_display(item.published_date)
                if item.published_date is not None else None
            ),
        })
    else:
        return HttpResponseBadRequest("Only supports html requests")


# pylint: disable=unused-argument
@require_GET
@login_required
def container_handler(request, usage_key_string):
    """
    The restful handler for container xblock requests.

    GET
        html: returns the HTML page for editing a container
        json: not currently supported
    """
    if 'text/html' in request.META.get('HTTP_ACCEPT', 'text/html'):

        usage_key = UsageKey.from_string(usage_key_string)
        try:
            course, xblock, __ = _get_item_in_course(request, usage_key)
        except ItemNotFoundError:
            return HttpResponseBadRequest()

        component_templates = get_component_templates(course)
        ancestor_xblocks = []
        parent = get_parent_xblock(xblock)
        while parent and parent.category != 'sequential':
            ancestor_xblocks.append(parent)
            parent = get_parent_xblock(parent)
        ancestor_xblocks.reverse()

        unit = ancestor_xblocks[0] if ancestor_xblocks else None
        unit_publish_state = compute_publish_state(unit) if unit else None

        return render_to_response('container.html', {
            'context_course': course,  # Needed only for display of menus at top of page.
            'xblock': xblock,
            'unit_publish_state': unit_publish_state,
            'xblock_locator': xblock.location,
            'unit': None if not ancestor_xblocks else ancestor_xblocks[0],
            'ancestor_xblocks': ancestor_xblocks,
            'component_templates': json.dumps(component_templates),
        })
    else:
        return HttpResponseBadRequest("Only supports html requests")


def get_component_templates(course):
    """
    Returns the applicable component templates that can be used by the specified course.
    """
    def create_template_dict(name, cat, boilerplate_name=None, is_common=False):
        """
        Creates a component template dict.

        Parameters
            display_name: the user-visible name of the component
            category: the type of component (problem, html, etc.)
            boilerplate_name: name of boilerplate for filling in default values. May be None.
            is_common: True if "common" problem, False if "advanced". May be None, as it is only used for problems.

        """
        return {
            "display_name": name,
            "category": cat,
            "boilerplate_name": boilerplate_name,
            "is_common": is_common
        }

    component_display_names = {
        'discussion': _("Discussion"),
        'html': _("HTML"),
        'problem': _("Problem"),
        'video': _("Video")
    }

    def get_component_display_name(component, default_display_name=None):
        """
        Returns the display name for the specified component.
        """
        component_class = _load_mixed_class(component)
        if hasattr(component_class, 'display_name') and component_class.display_name.default:
            return _(component_class.display_name.default)
        else:
            return default_display_name

    component_templates = []
    categories = set()
    # The component_templates array is in the order of "advanced" (if present), followed
    # by the components in the order listed in COMPONENT_TYPES.
    for category in COMPONENT_TYPES:
        templates_for_category = []
        component_class = _load_mixed_class(category)
        # add the default template with localized display name
        # TODO: Once mixins are defined per-application, rather than per-runtime,
        # this should use a cms mixed-in class. (cpennington)
        display_name = get_component_display_name(category, _('Blank'))
        templates_for_category.append(create_template_dict(display_name, category))
        categories.add(category)

        # add boilerplates
        if hasattr(component_class, 'templates'):
            for template in component_class.templates():
                filter_templates = getattr(component_class, 'filter_templates', None)
                if not filter_templates or filter_templates(template, course):
                    templates_for_category.append(
                        create_template_dict(
                            _(template['metadata'].get('display_name')),
                            category,
                            template.get('template_id'),
                            template['metadata'].get('markdown') is not None
                        )
                    )

        # Add any advanced problem types
        if category == 'problem':
            for advanced_problem_type in ADVANCED_PROBLEM_TYPES:
                component = advanced_problem_type['component']
                boilerplate_name = advanced_problem_type['boilerplate_name']
                component_display_name = get_component_display_name(component)
                templates_for_category.append(create_template_dict(component_display_name, component, boilerplate_name))
                categories.add(component)

        component_templates.append({
            "type": category,
            "templates": templates_for_category,
            "display_name": component_display_names[category]
            })

    # Check if there are any advanced modules specified in the course policy.
    # These modules should be specified as a list of strings, where the strings
    # are the names of the modules in ADVANCED_COMPONENT_TYPES that should be
    # enabled for the course.
    course_advanced_keys = course.advanced_modules
    advanced_component_templates = {"type": "advanced", "templates": [], "display_name": _("Advanced")}
    # Set component types according to course policy file
    if isinstance(course_advanced_keys, list):
        for category in course_advanced_keys:
            if category in ADVANCED_COMPONENT_TYPES and not category in categories:
                # boilerplates not supported for advanced components
                try:
                    component_display_name = get_component_display_name(category)
                    advanced_component_templates['templates'].append(
                        create_template_dict(
                            component_display_name,
                            category
                        )
                    )
                    categories.add(category)
                except PluginMissingError:
                    # dhm: I got this once but it can happen any time the
                    # course author configures an advanced component which does
                    # not exist on the server. This code here merely
                    # prevents any authors from trying to instantiate the
                    # non-existent component type by not showing it in the menu
                    log.warning(
                        "Advanced component %s does not exist. It will not be added to the Studio new component menu.",
                        category
                    )
                    pass
    else:
        log.error(
            "Improper format for course advanced keys! %s",
            course_advanced_keys
        )
    if len(advanced_component_templates['templates']) > 0:
        component_templates.insert(0, advanced_component_templates)

    return component_templates


@login_required
def _get_item_in_course(request, usage_key):
    """
    Helper method for getting the old location, containing course,
    item, and lms_link for a given locator.

    Verifies that the caller has permission to access this item.
    """
    # usage_key's course_key may have an empty run property
    usage_key = usage_key.replace(course_key=modulestore().fill_in_run(usage_key.course_key))

    course_key = usage_key.course_key

    if not has_course_access(request.user, course_key):
        raise PermissionDenied()

    course = modulestore().get_course(course_key)
    item = modulestore().get_item(usage_key, depth=1)
    lms_link = get_lms_link_for_item(item.location)

    return course, item, lms_link


@login_required
def component_handler(request, usage_key_string, handler, suffix=''):
    """
    Dispatch an AJAX action to an xblock

    Args:
        usage_id: The usage-id of the block to dispatch to
        handler (str): The handler to execute
        suffix (str): The remainder of the url to be passed to the handler

    Returns:
        :class:`django.http.HttpResponse`: The response from the handler, converted to a
            django response
    """

    usage_key = UsageKey.from_string(usage_key_string)

    descriptor = modulestore().get_item(usage_key)
    # Let the module handle the AJAX
    req = django_to_webob_request(request)

    try:
        resp = descriptor.handle(handler, req, suffix)

    except NoSuchHandlerError:
        log.info("XBlock %s attempted to access missing handler %r", descriptor, handler, exc_info=True)
        raise Http404

    # unintentional update to handle any side effects of handle call
    # could potentially be updating actual course data or simply caching its values
    modulestore().update_item(descriptor, request.user.id)

    return webob_to_django_response(resp)
