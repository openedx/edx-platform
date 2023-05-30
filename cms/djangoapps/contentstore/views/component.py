"""
Studio component views
"""


import logging
from urllib.parse import quote_plus

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseBadRequest
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey
from xblock.core import XBlock
from xblock.django.request import django_to_webob_request, webob_to_django_response
from xblock.exceptions import NoSuchHandlerError
from xblock.plugin import PluginMissingError
from xblock.runtime import Mixologist

from common.djangoapps.edxmako.shortcuts import render_to_response
from common.djangoapps.student.auth import has_course_author_access
from common.djangoapps.xblock_django.api import authorable_xblocks, disabled_xblocks
from common.djangoapps.xblock_django.models import XBlockStudioConfigurationFlag
from cms.djangoapps.contentstore.toggles import use_new_problem_editor
from openedx.core.lib.xblock_utils import get_aside_from_xblock, is_xblock_aside
from openedx.core.djangoapps.discussions.models import DiscussionsConfiguration
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.exceptions import ItemNotFoundError  # lint-amnesty, pylint: disable=wrong-import-order

from ..utils import get_lms_link_for_item, get_sibling_urls, reverse_course_url
from .helpers import get_parent_xblock, is_unit, xblock_type_display_name
from .block import StudioEditModuleRuntime, add_container_page_publishing_info, create_xblock_info

__all__ = [
    'container_handler',
    'component_handler'
]

log = logging.getLogger(__name__)

# NOTE: This list is disjoint from ADVANCED_COMPONENT_TYPES
COMPONENT_TYPES = ['discussion', 'library', 'html', 'openassessment', 'problem', 'video', 'drag-and-drop-v2']

ADVANCED_COMPONENT_TYPES = sorted({name for name, class_ in XBlock.load_classes()} - set(COMPONENT_TYPES))

ADVANCED_PROBLEM_TYPES = settings.ADVANCED_PROBLEM_TYPES

LIBRARY_BLOCK_TYPES = settings.LIBRARY_BLOCK_TYPES

CONTAINER_TEMPLATES = [
    "basic-modal", "modal-button", "edit-xblock-modal",
    "editor-mode-button", "upload-dialog",
    "add-xblock-component", "add-xblock-component-button", "add-xblock-component-menu",
    "add-xblock-component-support-legend", "add-xblock-component-support-level", "add-xblock-component-menu-problem",
    "xblock-string-field-editor", "xblock-access-editor", "publish-xblock", "publish-history",
    "unit-outline", "container-message", "container-access", "license-selector", "copy-clipboard-button",
    "edit-title-button",
]


def _advanced_component_types(show_unsupported):
    """
    Return advanced component types which can be created.

    Args:
        show_unsupported: if True, unsupported XBlocks may be included in the return value

    Returns:
        A dict of authorable XBlock types and their support levels (see XBlockStudioConfiguration). For example:
        {
            "done": "us",  # unsupported
            "discussion: "fs"  # fully supported
        }
        Note that the support level will be "True" for all XBlocks if XBlockStudioConfigurationFlag
        is not enabled.
    """
    enabled_block_types = _filter_disabled_blocks(ADVANCED_COMPONENT_TYPES)
    if XBlockStudioConfigurationFlag.is_enabled():
        authorable_blocks = authorable_xblocks(allow_unsupported=show_unsupported)
        filtered_blocks = {}
        for block in authorable_blocks:
            if block.name in enabled_block_types:
                filtered_blocks[block.name] = block.support_level
        return filtered_blocks
    else:
        all_blocks = {}
        for block_name in enabled_block_types:
            all_blocks[block_name] = True
        return all_blocks


def _load_mixed_class(category):
    """
    Load an XBlock by category name, and apply all defined mixins
    """
    component_class = XBlock.load_class(category)
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
            raise Http404  # lint-amnesty, pylint: disable=raise-missing-from
        with modulestore().bulk_operations(usage_key.course_key):
            try:
                course, xblock, lms_link, preview_lms_link = _get_item_in_course(request, usage_key)
            except ItemNotFoundError:
                return HttpResponseBadRequest()

            component_templates = get_component_templates(course)
            ancestor_xblocks = []
            parent = get_parent_xblock(xblock)
            action = request.GET.get('action', 'view')

            is_unit_page = is_unit(xblock)
            unit = xblock if is_unit_page else None

            is_first = True
            block = xblock

            # Build the breadcrumbs and find the ``Unit`` ancestor
            # if it is not the immediate parent.
            while parent:

                if unit is None and is_unit(block):
                    unit = block

                # add all to nav except current xblock page
                if xblock != block:
                    current_block = {
                        'title': block.display_name_with_default,
                        'children': parent.get_children(),
                        'is_last': is_first
                    }
                    is_first = False
                    ancestor_xblocks.append(current_block)

                block = parent
                parent = get_parent_xblock(parent)

            ancestor_xblocks.reverse()

            assert unit is not None, "Could not determine unit page"
            subsection = get_parent_xblock(unit)
            assert subsection is not None, "Could not determine parent subsection from unit " + str(
                unit.location)
            section = get_parent_xblock(subsection)
            assert section is not None, "Could not determine ancestor section from unit " + str(unit.location)

            # for the sequence navigator
            prev_url, next_url = get_sibling_urls(subsection, unit.location)
            # these are quoted here because they'll end up in a query string on the page,
            # and quoting with mako will trigger the xss linter...
            prev_url = quote_plus(prev_url) if prev_url else None
            next_url = quote_plus(next_url) if next_url else None

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
                'language_code': request.LANGUAGE_CODE,
                'context_course': course,  # Needed only for display of menus at top of page.
                'action': action,
                'xblock': xblock,
                'xblock_locator': xblock.location,
                'unit': unit,
                'is_unit_page': is_unit_page,
                'subsection': subsection,
                'section': section,
                'position': index,
                'prev_url': prev_url,
                'next_url': next_url,
                'new_unit_category': 'vertical',
                'outline_url': '{url}?format=concise'.format(url=reverse_course_url('course_handler', course.id)),
                'ancestor_xblocks': ancestor_xblocks,
                'component_templates': component_templates,
                'xblock_info': xblock_info,
                'draft_preview_link': preview_lms_link,
                'published_preview_link': lms_link,
                'templates': CONTAINER_TEMPLATES
            })
    else:
        return HttpResponseBadRequest("Only supports HTML requests")


def get_component_templates(courselike, library=False):  # lint-amnesty, pylint: disable=too-many-statements
    """
    Returns the applicable component templates that can be used by the specified course or library.
    """
    def create_template_dict(name, category, support_level, boilerplate_name=None, tab="common", hinted=False):
        """
        Creates a component template dict.

        Parameters
            display_name: the user-visible name of the component
            category: the type of component (problem, html, etc.)
            support_level: the support level of this component
            boilerplate_name: name of boilerplate for filling in default values. May be None.
            hinted: True if hinted problem else False
            tab: common(default)/advanced, which tab it goes in

        """
        return {
            "display_name": name,
            "category": category,
            "boilerplate_name": boilerplate_name,
            "hinted": hinted,
            "tab": tab,
            "support_level": support_level
        }

    def component_support_level(editable_types, name, template=None):
        """
        Returns the support level for the given xblock name/template combination.

        Args:
            editable_types: a QuerySet of xblocks with their support levels
            name: the name of the xblock
            template: optional template for the xblock

        Returns:
            If XBlockStudioConfigurationFlag is enabled, returns the support level
            (see XBlockStudioConfiguration) or False if this xblock name/template combination
            has no Studio support at all. If XBlockStudioConfigurationFlag is disabled,
            simply returns True.
        """
        # If the Studio support feature is disabled, return True for all.
        if not XBlockStudioConfigurationFlag.is_enabled():
            return True
        if template is None:
            template = ""
        extension_index = template.rfind(".yaml")
        if extension_index >= 0:
            template = template[0:extension_index]
        for block in editable_types:
            if block.name == name and block.template == template:
                return block.support_level

        return False

    def create_support_legend_dict():
        """
        Returns a dict of settings information for the display of the support level legend.
        """
        return {
            "show_legend": XBlockStudioConfigurationFlag.is_enabled(),
            "allow_unsupported_xblocks": allow_unsupported,
            "documentation_label": _("{platform_name} Support Levels:").format(platform_name=settings.PLATFORM_NAME)
        }

    component_display_names = {
        'discussion': _("Discussion"),
        'html': _("Text"),
        'problem': _("Problem"),
        'video': _("Video"),
        'openassessment': _("Open Response"),
        'library': _("Library Content"),
        'drag-and-drop-v2': _("Drag and Drop"),
    }

    component_templates = []
    categories = set()
    # The component_templates array is in the order of "advanced" (if present), followed
    # by the components in the order listed in COMPONENT_TYPES.
    component_types = COMPONENT_TYPES[:]

    # Libraries do not support discussions, drag-and-drop, and openassessment and other libraries
    component_not_supported_by_library = ['discussion', 'library', 'openassessment', 'drag-and-drop-v2']
    if library:
        component_types = [component for component in component_types
                           if component not in set(component_not_supported_by_library)]

    component_types = _filter_disabled_blocks(component_types)

    # Filter out discussion component from component_types if non-legacy discussion provider is configured for course
    component_types = _filter_discussion_for_non_legacy_provider(component_types, courselike.location.course_key)

    # Content Libraries currently don't allow opting in to unsupported xblocks/problem types.
    allow_unsupported = getattr(courselike, "allow_unsupported_xblocks", False)

    for category in component_types:  # lint-amnesty, pylint: disable=too-many-nested-blocks
        authorable_variations = authorable_xblocks(allow_unsupported=allow_unsupported, name=category)
        support_level_without_template = component_support_level(authorable_variations, category)
        templates_for_category = []
        component_class = _load_mixed_class(category)

        if support_level_without_template and category != 'library':
            # add the default template with localized display name
            # TODO: Once mixins are defined per-application, rather than per-runtime,
            # this should use a cms mixed-in class. (cpennington)
            template_id = None
            display_name = xblock_type_display_name(category, _('Blank'))  # this is the Blank Advanced problem
            # The ORA "blank" assessment should be Peer Assessment Only
            if category == 'openassessment':
                display_name = _("Peer Assessment Only")
                template_id = "peer-assessment"
            templates_for_category.append(
                create_template_dict(display_name, category, support_level_without_template, template_id, 'advanced')
            )
            categories.add(category)

        # add boilerplates
        if hasattr(component_class, 'templates'):
            for template in component_class.templates():
                filter_templates = getattr(component_class, 'filter_templates', None)
                if not filter_templates or filter_templates(template, courselike):
                    template_id = template.get('template_id')
                    support_level_with_template = component_support_level(
                        authorable_variations, category, template_id
                    )
                    if support_level_with_template:
                        # Tab can be 'common' 'advanced'
                        # Default setting is common/advanced depending on the presence of markdown
                        tab = 'common'
                        if template['metadata'].get('markdown') is None:
                            tab = 'advanced'
                        hinted = template.get('hinted', False)

                        templates_for_category.append(
                            create_template_dict(
                                _(template['metadata'].get('display_name')),  # lint-amnesty, pylint: disable=translation-of-non-string
                                category,
                                support_level_with_template,
                                template_id,
                                tab,
                                hinted,
                            )
                        )

        #If using new problem editor, we select problem type inside the editor
        # because of this, we only show one problem.
        if category == 'problem' and use_new_problem_editor():
            templates_for_category = [
                template for template in templates_for_category if template['boilerplate_name'] == 'blank_common.yaml'
            ]

        # Add any advanced problem types. Note that these are different xblocks being stored as Advanced Problems,
        # currently not supported in libraries .
        if category == 'problem' and not library and not use_new_problem_editor():
            disabled_block_names = [block.name for block in disabled_xblocks()]
            advanced_problem_types = [advanced_problem_type for advanced_problem_type in ADVANCED_PROBLEM_TYPES
                                      if advanced_problem_type['component'] not in disabled_block_names]
            for advanced_problem_type in advanced_problem_types:
                component = advanced_problem_type['component']
                boilerplate_name = advanced_problem_type['boilerplate_name']

                authorable_advanced_component_variations = authorable_xblocks(
                    allow_unsupported=allow_unsupported, name=component
                )
                advanced_component_support_level = component_support_level(
                    authorable_advanced_component_variations, component, boilerplate_name
                )
                if advanced_component_support_level:
                    try:
                        component_display_name = xblock_type_display_name(component)
                    except PluginMissingError:
                        log.warning('Unable to load xblock type %s to read display_name', component, exc_info=True)
                    else:
                        templates_for_category.append(
                            create_template_dict(
                                component_display_name,
                                component,
                                advanced_component_support_level,
                                boilerplate_name,
                                'advanced'
                            )
                        )
                        categories.add(component)

        # Add library block types.
        if category == 'library' and not library:
            disabled_block_names = [block.name for block in disabled_xblocks()]
            library_block_types = [problem_type for problem_type in LIBRARY_BLOCK_TYPES
                                   if problem_type['component'] not in disabled_block_names]
            for library_block_type in library_block_types:
                component = library_block_type['component']
                boilerplate_name = library_block_type['boilerplate_name']
                authorable_variations = authorable_xblocks(allow_unsupported=allow_unsupported, name=component)
                library_component_support_level = component_support_level(
                    authorable_variations, component, boilerplate_name
                )
                if library_component_support_level:
                    try:
                        component_display_name = xblock_type_display_name(component, default_display_name=component)
                    except PluginMissingError:
                        log.warning(
                            "Unable to load xblock type %s to read display_name",
                            component
                        )
                    else:
                        templates_for_category.append(
                            create_template_dict(
                                component_display_name,
                                component,
                                library_component_support_level,
                                boilerplate_name
                            )
                        )
                        categories.add(component)

        component_templates.append({
            "type": category,
            "templates": templates_for_category,
            "display_name": component_display_names[category],
            "support_legend": create_support_legend_dict()
        })

    # Libraries do not support advanced components at this time.
    if library:
        return component_templates

    # Check if there are any advanced modules specified in the course policy.
    # These modules should be specified as a list of strings, where the strings
    # are the names of the modules in ADVANCED_COMPONENT_TYPES that should be
    # enabled for the course.
    course_advanced_keys = courselike.advanced_modules
    advanced_component_templates = {
        "type": "advanced",
        "templates": [],
        "display_name": _("Advanced"),
        "support_legend": create_support_legend_dict()
    }
    advanced_component_types = _advanced_component_types(allow_unsupported)
    # Set component types according to course policy file
    if isinstance(course_advanced_keys, list):
        for category in course_advanced_keys:
            if category in advanced_component_types.keys() and category not in categories:  # pylint: disable=consider-iterating-dictionary
                # boilerplates not supported for advanced components
                try:
                    component_display_name = xblock_type_display_name(category, default_display_name=category)
                    advanced_component_templates['templates'].append(
                        create_template_dict(
                            component_display_name,
                            category,
                            advanced_component_types[category]
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
    if advanced_component_templates['templates']:
        component_templates.insert(0, advanced_component_templates)

    return component_templates


def _filter_discussion_for_non_legacy_provider(all_components, course_key):
    """
    Filter out Discussion component if non-legacy discussion provider is configured for course key
    """
    discussion_provider = DiscussionsConfiguration.get(context_key=course_key).provider_type

    if discussion_provider != 'legacy':
        filtered_components = [component for component in all_components if component != 'discussion']
    else:
        filtered_components = all_components

    return filtered_components


def _filter_disabled_blocks(all_blocks):
    """
    Filter out disabled xblocks from the provided list of xblock names.
    """
    disabled_block_names = [block.name for block in disabled_xblocks()]
    return [block_name for block_name in all_blocks if block_name not in disabled_block_names]


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

    # Let the block handle the AJAX
    req = django_to_webob_request(request)

    try:
        if is_xblock_aside(usage_key):
            # Get the descriptor for the block being wrapped by the aside (not the aside itself)
            descriptor = modulestore().get_item(usage_key.usage_key)
            handler_descriptor = get_aside_from_xblock(descriptor, usage_key.aside_type)
            asides = [handler_descriptor]
        else:
            descriptor = modulestore().get_item(usage_key)
            handler_descriptor = descriptor
            asides = []
        handler_descriptor.xmodule_runtime = StudioEditModuleRuntime(request.user)
        resp = handler_descriptor.handle(handler, req, suffix)
    except NoSuchHandlerError:
        log.info("XBlock %s attempted to access missing handler %r", handler_descriptor, handler, exc_info=True)
        raise Http404  # lint-amnesty, pylint: disable=raise-missing-from

    # unintentional update to handle any side effects of handle call
    # could potentially be updating actual course data or simply caching its values
    # Addendum:
    # TNL 101-62 studio write permission is also checked for editing content.

    if has_course_author_access(request.user, usage_key.course_key):
        modulestore().update_item(descriptor, request.user.id, asides=asides)
    else:
        #fail quietly if user is not course author.
        log.warning(
            "%s does not have have studio write permissions on course: %s. write operations not performed on %r",
            request.user.id,
            usage_key.course_key,
            handler
        )

    return webob_to_django_response(resp)
