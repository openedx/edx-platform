from __future__ import absolute_import

import logging

from django.http import HttpResponseBadRequest, Http404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.core.exceptions import PermissionDenied
from django.conf import settings
from opaque_keys import InvalidKeyError
from xmodule.modulestore.exceptions import ItemNotFoundError
from edxmako.shortcuts import render_to_response

from xmodule.modulestore.django import modulestore

from xblock.core import XBlock
from xblock.django.request import webob_to_django_response, django_to_webob_request
from xblock.exceptions import NoSuchHandlerError
from xblock.fields import Scope
from xblock.plugin import PluginMissingError
from xblock.runtime import Mixologist

from contentstore.utils import get_lms_link_for_item
from contentstore.views.helpers import get_parent_xblock, is_unit, xblock_type_display_name
from contentstore.views.item import create_xblock_info, add_container_page_publishing_info, StudioEditModuleRuntime

from opaque_keys.edx.keys import UsageKey

from util.keyword_substitution import get_keywords_supported
from student.auth import has_course_author_access
from django.utils.translation import ugettext as _
from models.settings.course_grading import CourseGradingModel

__all__ = ['OPEN_ENDED_COMPONENT_TYPES',
           'ADVANCED_COMPONENT_POLICY_KEY',
           'container_handler',
           'component_handler'
           ]

log = logging.getLogger(__name__)

# NOTE: it is assumed that this list is disjoint from ADVANCED_COMPONENT_TYPES
COMPONENT_TYPES = ['discussion', 'html', 'problem', 'video']

# Constants for determining if these components should be enabled for this course
SPLIT_TEST_COMPONENT_TYPE = 'split_test'
OPEN_ENDED_COMPONENT_TYPES = ["combinedopenended", "peergrading"]
NOTE_COMPONENT_TYPES = ['notes']

if settings.FEATURES.get('ALLOW_ALL_ADVANCED_COMPONENTS'):
    ADVANCED_COMPONENT_TYPES = sorted(set(name for name, class_ in XBlock.load_classes()) - set(COMPONENT_TYPES))
else:
    ADVANCED_COMPONENT_TYPES = settings.ADVANCED_COMPONENT_TYPES
XBLOCKS_ALWAYS_IN_STUDIO = getattr(settings, 'XBLOCKS_ALWAYS_IN_STUDIO', [])

ADVANCED_COMPONENT_CATEGORY = 'advanced'
ADVANCED_COMPONENT_POLICY_KEY = 'advanced_modules'

ADVANCED_PROBLEM_TYPES = settings.ADVANCED_PROBLEM_TYPES


CONTAINER_TEMPLATES = [
    "basic-modal", "modal-button", "edit-xblock-modal",
    "editor-mode-button", "upload-dialog",
    "add-xblock-component", "add-xblock-component-button", "add-xblock-component-menu",
    "add-xblock-component-menu-problem", "xblock-string-field-editor", "publish-xblock", "publish-history",
    "unit-outline", "container-message", "license-selector",
]


def _advanced_component_types():
    """
    Return advanced component types which can be created.
    """
    return [c_type for c_type in ADVANCED_COMPONENT_TYPES if c_type not in settings.DEPRECATED_ADVANCED_COMPONENT_TYPES]


def _load_mixed_class(category):
    """
    Load an XBlock by category name, and apply all defined mixins
    """
    component_class = XBlock.load_class(category, select=settings.XBLOCK_SELECT_FUNCTION)
    mixologist = Mixologist(settings.XBLOCK_MIXINS)
    return mixologist.mix(component_class)


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

        try:
            usage_key = UsageKey.from_string(usage_key_string)
        except InvalidKeyError:  # Raise Http404 on invalid 'usage_key_string'
            raise Http404
        with modulestore().bulk_operations(usage_key.course_key):
            try:
                course, xblock, lms_link, preview_lms_link = _get_item_in_course(request, usage_key)
            except ItemNotFoundError:
                return HttpResponseBadRequest()

            component_templates = get_component_templates(course)
            ancestor_xblocks = []
            parent = get_parent_xblock(xblock)
            action = request.REQUEST.get('action', 'view')

            is_unit_page = is_unit(xblock)
            unit = xblock if is_unit_page else None

            while parent and parent.category != 'course':
                if unit is None and is_unit(parent):
                    unit = parent
                ancestor_xblocks.append(parent)
                parent = get_parent_xblock(parent)
            ancestor_xblocks.reverse()

            assert unit is not None, "Could not determine unit page"
            subsection = get_parent_xblock(unit)
            assert subsection is not None, "Could not determine parent subsection from unit " + unicode(unit.location)
            section = get_parent_xblock(subsection)
            assert section is not None, "Could not determine ancestor section from unit " + unicode(unit.location)

            # Fetch the XBlock info for use by the container page. Note that it includes information
            # about the block's ancestors and siblings for use by the Unit Outline.
            xblock_info = create_xblock_info(xblock, include_ancestor_info=is_unit_page)

            if is_unit_page:
                add_container_page_publishing_info(xblock, xblock_info)

            # need to figure out where this item is in the list of children as the
            # preview will need this
            index = 1
            for child in subsection.get_children():
                if child.location == unit.location:
                    break
                index += 1

            return render_to_response('container.html', {
                'context_course': course,  # Needed only for display of menus at top of page.
                'action': action,
                'xblock': xblock,
                'xblock_locator': xblock.location,
                'unit': unit,
                'is_unit_page': is_unit_page,
                'subsection': subsection,
                'section': section,
                'new_unit_category': 'vertical',
                'ancestor_xblocks': ancestor_xblocks,
                'component_templates': component_templates,
                'xblock_info': xblock_info,
                'draft_preview_link': preview_lms_link,
                'published_preview_link': lms_link,
                'keywords_supported': get_keywords_supported(),
                'templates': CONTAINER_TEMPLATES
            })
    else:
        return HttpResponseBadRequest("Only supports HTML requests")


def get_component_templates(courselike, library=False):
    """
    Returns the applicable component templates that can be used by the specified course or library.
    """
    def create_template_dict(name, cat, boilerplate_name=None, tab="common", hinted=False):
        """
        Creates a component template dict.

        Parameters
            display_name: the user-visible name of the component
            category: the type of component (problem, html, etc.)
            boilerplate_name: name of boilerplate for filling in default values. May be None.
            hinted: True if hinted problem else False
            tab: common(default)/advanced, which tab it goes in

        """
        return {
            "display_name": name,
            "category": cat,
            "boilerplate_name": boilerplate_name,
            "hinted": hinted,
            "tab": tab
        }

    component_display_names = {
        'discussion': _("Discussion"),
        'html': _("HTML"),
        'problem': _("Problem"),
        'video': _("Video")
    }

    component_templates = []
    categories = set()
    # The component_templates array is in the order of "advanced" (if present), followed
    # by the components in the order listed in COMPONENT_TYPES.
    component_types = COMPONENT_TYPES[:]

    # Libraries do not support discussions
    if library:
        component_types = [component for component in component_types if component != 'discussion']

    for category in component_types:
        templates_for_category = []
        component_class = _load_mixed_class(category)
        # add the default template with localized display name
        # TODO: Once mixins are defined per-application, rather than per-runtime,
        # this should use a cms mixed-in class. (cpennington)
        display_name = xblock_type_display_name(category, _('Blank'))  # this is the Blank Advanced problem
        templates_for_category.append(create_template_dict(display_name, category, None, 'advanced'))
        categories.add(category)

        # add boilerplates
        if hasattr(component_class, 'templates'):
            for template in component_class.templates():
                filter_templates = getattr(component_class, 'filter_templates', None)
                if not filter_templates or filter_templates(template, courselike):
                    # Tab can be 'common' 'advanced'
                    # Default setting is common/advanced depending on the presence of markdown
                    tab = 'common'
                    if template['metadata'].get('markdown') is None:
                        tab = 'advanced'
                    hinted = template.get('hinted', False)

                    templates_for_category.append(
                        create_template_dict(
                            _(template['metadata'].get('display_name')),    # pylint: disable=translation-of-non-string
                            category,
                            template.get('template_id'),
                            tab,
                            hinted,
                        )
                    )

        # Add any advanced problem types
        if category == 'problem':
            for advanced_problem_type in ADVANCED_PROBLEM_TYPES:
                component = advanced_problem_type['component']
                boilerplate_name = advanced_problem_type['boilerplate_name']
                try:
                    component_display_name = xblock_type_display_name(component)
                except PluginMissingError:
                    log.warning('Unable to load xblock type %s to read display_name', component, exc_info=True)
                else:
                    templates_for_category.append(
                        create_template_dict(component_display_name, component, boilerplate_name, 'advanced')
                    )
                    categories.add(component)

        component_templates.append({
            "type": category,
            "templates": templates_for_category,
            "display_name": component_display_names[category]
        })

    # Libraries do not support advanced components at this time.
    if library:
        return component_templates

    # Check if there are any advanced modules specified in the course policy.
    # These modules should be specified as a list of strings, where the strings
    # are the names of the modules in ADVANCED_COMPONENT_TYPES that should be
    # enabled for the course.
    course_advanced_keys = courselike.advanced_modules
    advanced_component_templates = {"type": "advanced", "templates": [], "display_name": _("Advanced")}
    advanced_component_types = _advanced_component_types()
    # Set component types according to course policy file
    course_advanced_keys = course_advanced_keys or []
    course_advanced_keys = list(set(course_advanced_keys + XBLOCKS_ALWAYS_IN_STUDIO))
    if isinstance(course_advanced_keys, list):
        for category in course_advanced_keys:
            if category in advanced_component_types and category not in categories:
                # boilerplates not supported for advanced components
                try:
                    component_display_name = xblock_type_display_name(category, default_display_name=category)
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
    item, lms_link, and preview_lms_link for a given locator.

    Verifies that the caller has permission to access this item.
    """
    # usage_key's course_key may have an empty run property
    usage_key = usage_key.replace(course_key=modulestore().fill_in_run(usage_key.course_key))

    course_key = usage_key.course_key

    if not has_course_author_access(request.user, course_key):
        raise PermissionDenied()

    course = modulestore().get_course(course_key)
    item = modulestore().get_item(usage_key, depth=1)
    lms_link = get_lms_link_for_item(item.location)
    preview_lms_link = get_lms_link_for_item(item.location, preview=True)

    return course, item, lms_link, preview_lms_link


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
    descriptor.xmodule_runtime = StudioEditModuleRuntime(request.user)
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
