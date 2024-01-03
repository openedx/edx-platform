"""
LibraryContent: The XBlock used to include blocks from a library in a course.
"""
from __future__ import annotations

import json
import logging
import random
from copy import copy
from gettext import ngettext, gettext
from typing import TYPE_CHECKING

import bleach
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.utils.functional import classproperty
from lxml import etree
from lxml.etree import XMLSyntaxError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import LibraryLocator, LibraryLocatorV2
from opaque_keys.edx.keys import UsageKey
from rest_framework import status
from web_fragments.fragment import Fragment
from webob import Response
from xblock.completable import XBlockCompletionMode
from xblock.core import XBlock
from xblock.exceptions import JsonHandlerError
from xblock.fields import Boolean, Integer, List, Scope, String

from xmodule.capa.responsetypes import registry
from xmodule.mako_block import MakoTemplateBlockBase
from xmodule.studio_editable import StudioEditableBlock
from xblockutils.studio_editable import StudioEditableXBlockMixin
from xmodule.util.builtin_assets import add_webpack_js_to_fragment
from xmodule.validation import StudioValidation, StudioValidationMessage
from xmodule.xml_block import XmlMixin
from xmodule.x_module import (
    STUDENT_VIEW,
    ResourceTemplates,
    XModuleMixin,
    XModuleToXBlockMixin,
    shim_xmodule_js,
)


if TYPE_CHECKING:
    # This class is only needed for a type annotation.
    # To avoid circular import, only import it for type checking.
    from xmodule.library_tools import LibraryToolsService


# Make '_' a no-op so we can scrape strings. Using lambda instead of
#  `django.utils.translation.ugettext_noop` because Django cannot be imported in this file
_ = lambda text: text

logger = logging.getLogger(__name__)

ANY_CAPA_TYPE_VALUE = 'any'


def _get_human_name(problem_class):
    """
    Get the human-friendly name for a problem type.
    """
    return getattr(problem_class, 'human_name', problem_class.__name__)


def _get_capa_types():
    """
    Gets capa types tags and labels
    """
    capa_types = {tag: _get_human_name(registry.get_class_for_tag(tag)) for tag in registry.registered_tags()}

    return [{'value': ANY_CAPA_TYPE_VALUE, 'display_name': _('Any Type')}] + sorted([
        {'value': capa_type, 'display_name': caption}
        for capa_type, caption in capa_types.items()
    ], key=lambda item: item.get('display_name'))


class LibraryToolsUnavailable(ValueError):
    """
    Raised when the library_tools service is requested in a runtime that doesn't provide it.
    """
    def __init__(self):
        super().__init__("Needed 'library_tools' features which were not available in the current runtime")


@XBlock.wants('library_tools')  # TODO: Split this service into its LMS and CMS parts.
@XBlock.wants('studio_user_permissions')  # Only available in CMS.
@XBlock.wants('user')
@XBlock.needs('mako')
class LibraryContentBlock(
    XmlMixin,
    MakoTemplateBlockBase,
    StudioEditableXBlockMixin,
    XModuleToXBlockMixin,
    ResourceTemplates,
    XModuleMixin,
    StudioEditableBlock,
):
    """
    An XBlock whose children are chosen dynamically from a content library.
    Can be used to create randomized assessments among other things.

    Note: technically, all matching blocks from the content library are added
    as children of this block, but only a subset of those children are shown to
    any particular student.
    """
    # pylint: disable=abstract-method

    editable_fields = ("candidates",)
    has_children = True
    has_author_view = True

    resources_dir = 'assets/library_content'

    mako_template = 'widgets/metadata-edit.html'
    studio_js_module_name = "VerticalDescriptor"

    show_in_read_only_mode = True

    # noinspection PyMethodParameters
    @classproperty
    def completion_mode(cls):  # pylint: disable=no-self-argument
        """
        Allow overriding the completion mode with a feature flag.
        This is a property, so it can be dynamically overridden in tests, as it is not evaluated at runtime.
        """
        if settings.FEATURES.get('MARK_LIBRARY_CONTENT_BLOCK_COMPLETE_ON_VIEW', False):
            return XBlockCompletionMode.COMPLETABLE

        return XBlockCompletionMode.AGGREGATOR

    resources_dir = 'assets/library_content'

    display_name = String(
        display_name=_("Display Name"),
        help=_("The display name for this component."),
        default="Library Content",
        scope=Scope.settings,
    )
    source_library_id = String(
        display_name=_("Library"),
        help=_("Select the library from which you want to draw content."),
        scope=Scope.settings,
        values_provider=lambda instance: instance.source_library_values(),
    )
    source_library_version = String(
        # This is a hidden field that stores the version of source_library when we last pulled content from it
        display_name=_("Library Version"),
        scope=Scope.settings,
    )
    max_count = Integer(
        display_name=_("Count"),
        help=_("Enter the number of components to display to each student. Set it to -1 to display all components."),
        default=1,
        scope=Scope.settings,
    )
    capa_type = String(
        display_name=_("Problem Type"),
        help=_('Choose a problem type to fetch from the library. If "Any Type" is selected no filtering is applied.'),
        default=ANY_CAPA_TYPE_VALUE,
        values=_get_capa_types(),
        scope=Scope.settings,
    )
    candidates = List(
        # This is a list of (block_type, block_id) used to record the set of blocks
        # which are candidates for the selected list.
        display_name=_("Manually Selected Blocks"),
        default=[],
        scope=Scope.settings,
    )
    selected = List(
        # This is a list of (block_type, block_id) tuples used to record
        # which set of matching blocks was selected per user
        default=[],
        scope=Scope.user_state,
    )
    shuffle = Boolean(
        # Do we shuffle (randomize order) of selected blocks for each learner?
        # True -> Order is randomized for each learner. \n False -> Original order from candidates/children is used.
        # False -> is the block content only drawn from content which is in the candidates list?
        display_name=_("Shuffle Components"),
        help=_("When enabled, each learner will see the components in a randomized order."),
        default=True,
        scope=Scope.settings,

    )
    manual = Boolean(
        # Should selected blocks be limited to the manually-picked candidates?
        # True -> Draw selections from `candidates`.
        # False -> Draw selections from `children`.
        display_name=_("Limit Components to Selection"),
        help=_("When enabled, only the checked-off components on the 'View' page are available to learners."),
        default=False,
        scope=Scope.settings,
    )
    # This cannot be called `show_reset_button`, because children blocks inherit this as a default value.
    allow_resetting_children = Boolean(
        display_name=_("Show Reset Button"),
        help=_("Determines whether a 'Reset Problems' button is shown, so users may reset their answers and reshuffle "
               "selected items."),
        scope=Scope.settings,
        default=False
    )

    @property
    def source_library_key(self):
        """
        Convenience method to get the library ID as a LibraryLocator and not just a string.

        Supports either library v1 or library v2 locators.
        """
        try:
            return LibraryLocator.from_string(self.source_library_id)
        except InvalidKeyError:
            return LibraryLocatorV2.from_string(self.source_library_id)

    @property
    def non_editable_metadata_fields(self):
        """
        This variable contains a list of the XBlock fields that should not be displayed in the Studio editor.
        """
        non_editable_fields = super().non_editable_metadata_fields
        non_editable_fields.extend([
            LibraryContentBlock.source_library_version,
            LibraryContentBlock.candidates,
        ])
        return non_editable_fields

    def _publish_event(self, event_name, result, **kwargs):
        """
        Helper method to publish an event for analytics purposes
        """
        event_data = {
            "location": str(self.location),
            "result": result,
            "previous_count": getattr(self, "_last_event_result_count", len(self.selected)),
            "max_count": self.max_count,
        }
        event_data.update(kwargs)
        self.runtime.publish(self, f"edx.librarycontentblock.content.{event_name}", event_data)
        self._last_event_result_count = len(result)  # pylint: disable=attribute-defined-outside-init

    def available_children(self) -> list[tuple[str, str]]:
        """
        Returns (block_type, block_id) tuples which children are possible for selection,
        in the original order from the candidates list (if manual) or lib-copied children list (if not).
        """
        return self._available_children(
            library_children=self.children,
            candidates=list(map(tuple, self.candidates)),  # Convert from nested list to list-of-tuples.
            manual=self.manual,
        )

    @classmethod
    def _available_children(
        cls,
        library_children: list[UsageKey],
        candidates: list[tuple[str, str]],
        manual: bool,
    ) -> list[tuple[str, str]]:
        """
        Static implementation of available_children.
        """
        children = [(child.block_type, child.block_id) for child in library_children]
        if manual:
            return [candidate for candidate in candidates if candidate in children]
        else:
            return children

    @classmethod
    def make_selection(
        cls,
        old_selected: list[tuple[str, str]],
        library_children: list[UsageKey],
        candidates: list[tuple[str, str]],
        max_count: int,
        manual: bool,
        shuffle: bool,
    ) -> dict[str, list]:
        """
        Dynamically selects block_ids indicating which of the possible children are displayed to the current user.
        The blocks returned are kept consistent for a user,
        unless changes have been made to the library's contents or the settings of the block.
        Returns:
            A dict containing the following keys:
            'selected' (list) of (block_type, block_id) tuples assigned to this student
            'invalid' (list) of dropped (block_type, block_id) tuples that are no longer valid
            'overlimit' (list) of dropped (block_type, block_id) tuples that were previously selected
            'added' (list) of newly added (block_type, block_id) tuples

        When generating randomized content to show to a user, we want the following user experince:
        1. When a learner first interacts with the block, they are shown N items from the children at random.
        2. Every subsequent time they view that content, they are given the same content,
        unless one of the below conditions is met:
            a. The max_count is increased, requiring the learner to see more.
            b. The max_count is decreased, requiring the learner to see less content.
            c. When blocks previously assigned to a learner are deleted.
        3. In case a, we take the selected blocks that were valid before the edit,
            and supplament those with new blocks chosen at random until the number of blocks is max_count
        4. In case b, we take the selected blocks that were valid before the edit,
            and remove blocks randomly until he number of blocks is max_count.
        5. In case c, we remove the blocks that are now invalid,
           and supplament those remaining with new blocks chosen at random until the number of blocks is max_count.

        When generating manully selected content, we want all users to see all the items selected.
        size, however, limits the amount of content shown.
        """
        selected: list[tuple[str, str]] = old_selected.copy()
        available: list[tuple[str, str]] = cls._available_children(library_children, candidates, manual)

        # Remove blocks from selection if they're no longer candidates/children.
        selected = [block for block in selected if block in available]
        invalid: set[tuple[str, str]] = set(old_selected) - set(selected)

        # Remove or add blocks if we don't have the correct number in the selection.
        additions: set[tuple[str, str]] = set()
        overlimit: set[tuple[str, str]] = set()
        desired_size: int = min(max_count, len(available)) if max_count >= 0 else len(available)
        if len(selected) > desired_size:
            num_to_remove = len(selected) - desired_size
            overlimit = set(random.sample(selected, num_to_remove))
            selected = [block for block in selected if block not in overlimit]
        elif len(selected) < desired_size:
            num_to_add = desired_size - len(selected)
            available_additions: set[tuple[str, str]] = set(available) - set(selected)
            additions = set(random.sample(available_additions, num_to_add))
            selected = [block for block in available if block in (additions | set(selected))]

        # If we've made any change AND if shuffling is enabled, then re-shuffle.
        # In other words, always shuffle UNLESS:
        #  * no changes have been made (because we don't want to re-order a learner's blocks for no reason); OR
        #  * shuffling is disabled (the code above ensures that we're using the order from the library).
        # Otherwise, use the pre-existing order.
        if shuffle and (invalid or overlimit or additions):
            random.shuffle(selected)

        # return lists because things get json serialized down the line.
        return {
            'selected': selected,
            'invalid': list(invalid),
            'overlimit': list(overlimit),
            'added': list(additions),
        }

    @classmethod
    def publish_selected_children_events(cls, block_keys, format_block_keys, publish_event):
        """
        Helper method for publishing events when children blocks are
        selected/updated for a user.  This helper is also used by
        the ContentLibraryTransformer.

        Arguments:

            block_keys -
                A dict describing which events to publish (add or
                remove), see `make_selection` above for format details.

            format_block_keys -
                A function to convert block keys to the format expected
                by publish_event. Must have the signature:

                    [(block_type, block_id)] -> T

                Where T is a collection of block keys as accepted by
                `publish_event`.

            publish_event -
                Function that handles the actual publishing.  Must have
                the signature:

                    <'removed'|'assigned'> -> result:T -> removed:T -> reason:str -> None

                Where T is a collection of block_keys as returned by
                `format_block_keys`.
        """
        if block_keys['invalid']:
            # reason "invalid" means deleted from library or a different library is now being used.
            publish_event(
                "removed",
                result=format_block_keys(block_keys['selected']),
                removed=format_block_keys(block_keys['invalid']),
                reason="invalid"
            )

        if block_keys['overlimit']:
            publish_event(
                "removed",
                result=format_block_keys(block_keys['selected']),
                removed=format_block_keys(block_keys['overlimit']),
                reason="overlimit"
            )

        if block_keys['added']:
            publish_event(
                "assigned",
                result=format_block_keys(block_keys['selected']),
                added=format_block_keys(block_keys['added'])
            )

    def selected_children(self):
        """
        Returns a [] of block_ids indicating which of the possible children
        have been selected to display to the current user.

        This reads and updates the "selected" field, which has user_state scope.

        Note: the return value (self.selected) contains block_ids. To get
        actual BlockUsageLocators, it is necessary to use self.children,
        because the block_ids alone do not specify the block type.
        """
        max_count = self.max_count
        if max_count < 0:
            max_count = len(self.children)
        block_keys = self.make_selection(
            old_selected=list(map(tuple, self.selected)),  # Convert from nested list to list-of-tuples.
            library_children=self.children,
            candidates=list(map(tuple, self.candidates)),  # Convert from nested list to list-of-tuples.
            max_count=self.max_count,
            manual=self.manual,
            shuffle=self.shuffle,
        )

        # Publish events for analytics purposes:
        lib_tools = self.get_tools()
        format_block_keys = lambda keys: lib_tools.create_block_analytics_summary(self.location.course_key, keys)
        self.publish_selected_children_events(
            block_keys,
            format_block_keys,
            self._publish_event,
        )

        if any(block_keys[changed] for changed in ('invalid', 'overlimit', 'added')):
            # Save our selections to the user state, to ensure consistency:
            selected = block_keys['selected']
            self.selected = selected  # TODO: this doesn't save from the LMS "Progress" page.

        return self.selected

    @XBlock.handler
    def reset_selected_children(self, _, __):
        """
        Resets the XBlock's state for a user.

        This resets the state of all `selected` children and then clears the `selected` field
        so that the new blocks are randomly chosen for this user.
        """
        if not self.allow_resetting_children:
            return Response('"Resetting selected children" is not allowed for this XBlock',
                            status=status.HTTP_400_BAD_REQUEST)

        for block_type, block_id in self.selected_children():
            block = self.runtime.get_block(self.location.course_key.make_usage_key(block_type, block_id))
            if hasattr(block, 'reset_problem'):
                block.reset_problem(None)
                block.save()

        self.selected = []
        return Response(json.dumps(self.student_view({}).content))

    def _get_selected_child_blocks(self):
        """
        Generator returning XBlock instances of the children selected for the
        current user.
        """
        for block_type, block_id in self.selected_children():
            yield self.runtime.get_block(self.location.course_key.make_usage_key(block_type, block_id))

    def student_view(self, context):  # lint-amnesty, pylint: disable=missing-function-docstring
        """
        Renders the view that learners see.
        """
        fragment = Fragment()
        contents = []
        child_context = {} if not context else copy(context)

        for child in self._get_selected_child_blocks():
            if child is None:
                # TODO: Fix the underlying issue in TNL-7424
                # This shouldn't be happening, but does for an as-of-now
                # unknown reason. Until we address the underlying issue,
                # let's at least log the error explicitly, ignore the
                # exception, and prevent the page from resulting in a
                # 500-response.
                logger.error('Skipping display for child block that is None')
                continue

            rendered_child = child.render(STUDENT_VIEW, child_context)
            fragment.add_fragment_resources(rendered_child)
            contents.append({
                'id': str(child.location),
                'content': rendered_child.content,
            })

        fragment.add_content(self.runtime.service(self, 'mako').render_lms_template('vert_module.html', {
            'items': contents,
            'xblock_context': context,
            'show_bookmark_button': False,
            'watched_completable_blocks': set(),
            'completion_delay_ms': None,
            'reset_button': self.allow_resetting_children,
        }))

        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/library_content_reset.js'))
        fragment.initialize_js('LibraryContentReset')
        return fragment

    def author_view(self, context):
        """
        Renders the Studio views.
        Normal studio view: If block is properly configured, displays library status summary
        Studio container view: displays a preview of all possible children.
        """
        fragment = Fragment()
        root_xblock = context.get('root_xblock')
        is_root = root_xblock and root_xblock.location == self.location
        try:
            is_updating = self.get_tools().are_children_syncing(self)
        except LibraryToolsUnavailable:
            is_updating = False
        if is_root and not is_updating:
            # User has clicked the "View" link. Show a preview of all possible children:
            if self.children:  # pylint: disable=no-member
                max_count = self.max_count
                if max_count < 0:
                    max_count = len(self.children)
                context = {} if not context else copy(context)
                context['can_edit_visibility'] = False
                context['can_move'] = False
                context['can_collapse'] = True
                context['selectable'] = True
                self.render_children(context, fragment, can_reorder=False, can_add=False)
        # else: When shown on a unit page, don't show any sort of preview -
        # just the status of this block in the validation area.
        context['is_loading'] = is_updating

        # The following JS is used to make the "Update now" button work on the unit page and the container view:
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/library_content_edit.js'))
        fragment.initialize_js('LibraryContentAuthorView')
        return fragment

    def studio_view(self, _context):
        """
        Render a form for editing this XBlock
        """
        fragment = Fragment(
            self.runtime.service(self, 'mako').render_template(self.mako_template, self.get_context())
        )
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/library_content_edit_helpers.js'))
        add_webpack_js_to_fragment(fragment, 'LibraryContentBlockEditor')
        shim_xmodule_js(fragment, self.studio_js_module_name)
        return fragment

    def get_child_blocks(self):
        """
        Return only the subset of our children relevant to the current student.
        """
        return list(self._get_selected_child_blocks())

    def get_tools(self, to_read_library_content: bool = False) -> LibraryToolsService:
        """
        Grab the library tools service and confirm that it'll work for us. Else, raise LibraryToolsUnavailable.
        """
        if tools := self.runtime.service(self, 'library_tools'):
            if (not to_read_library_content) or tools.can_use_library_content(self):
                return tools
        raise LibraryToolsUnavailable()

    def get_user_id(self):
        """
        Get the ID of the current user.
        """
        user_service = self.runtime.service(self, 'user')
        if user_service:
            # May be None when creating bok choy test fixtures
            user_id = user_service.get_current_user().opt_attrs.get('edx-platform.user_id', None)
        else:
            user_id = None
        return user_id

    def render_children(self, context, fragment, can_reorder=False, can_add=False):
        """
        Renders the children of the module with HTML appropriate for Studio. If can_reorder is True,
        then the children will be rendered to support drag and drop.
        """
        contents = []
        for child in self.get_children():  # pylint: disable=no-member
            if can_reorder:
                context['reorderable_items'].add(child.location)
            context['can_add'] = can_add

            context['is_selected'] = [child.location.block_type, child.location.block_id] in self.candidates
            rendered_child = child.render(StudioEditableBlock.get_preview_view_name(child), context)
            fragment.add_fragment_resources(rendered_child)
            contents.append({
                'id': str(child.location),
                'content': rendered_child.content
            })

        fragment.add_content(self.runtime.service(self, 'mako').render_template("studio_render_children_view.html", {  # pylint: disable=no-member
            'items': contents,
            'xblock_context': context,
            'can_add': can_add,
            'can_reorder': can_reorder,
        }))

    def _validate_sync_permissions(self):
        """
        Raises PermissionDenied() if we can't confirm that user has write on this block and read on source library.

        If source library isn't set, then that's OK.
        """
        if not (user_perms := self.runtime.service(self, 'studio_user_permissions')):
            raise PermissionDenied("Access cannot be validated in the current runtime.")
        if not user_perms.can_write(self.scope_ids.usage_id.context_key):
            raise PermissionDenied(f"Cannot write to block at {self.scope_ids.usage_id}")
        if self.source_library_key:
            if not user_perms.can_read(self.source_library_key):
                raise PermissionDenied(f"Cannot read library at {self.source_library_key}")

    # suffix argument is specified for xblocks, but we are not using herein
    @XBlock.json_handler
    def submit_studio_edits(self, data, suffix=''):  # pylint: disable=unused-argument
        """
        Ajax handler for submiting changes to the candidates list.
        Cleans them to be of type List[tuple[str,str]]
        where the tuple is (block_type, block_id)
        """
        if list(data['values'].keys()) != list(self.editable_fields):
            raise JsonHandlerError(
                400,
                "Library Content Block only supports the editing of the candidates field  with this handler."
            )
        usage_key_list = [UsageKey.from_string(usage_key_string) for usage_key_string in data['values']['candidates']]
        self.candidates = [(usage_key.block_type, usage_key.block_id) for usage_key in usage_key_list]

    @XBlock.handler
    def get_block_ids(self, request, suffix=''):  # lint-amnesty, pylint: disable=unused-argument
        """
        Return candidates for selection.
        """
        # construct usage_key list from library children so it is fully formed.
        usage_key_list = [child for child in self.children if [child.block_type, child.block_id] in self.candidates]
        return Response(json.dumps({'candidates': [str(usage_key) for usage_key in usage_key_list]}))

    @XBlock.handler
    def upgrade_and_sync(self, request=None, suffix=None):  # pylint: disable=unused-argument
        """
        HTTP handler allowing Studio users to update to latest version of source library and synchronize children.

        This is a thin wrapper around `sync_from_library(upgrade_to_latest=True)`, plus permission checks.

        Returns 400 if libraray tools or user permission services are not available.
        Returns 403/404 if user lacks read access on source library or write access on this block.
        """
        self._validate_sync_permissions()
        if not self.source_library_id:
            return Response(_("Source content library has not been specified."), status=400)
        try:
            self.sync_from_library(upgrade_to_latest=True)
        except LibraryToolsUnavailable:
            return Response(_("Content libraries are not available in the current runtime."), status=400)
        except ObjectDoesNotExist:
            return Response(
                _("Source content library does not exist: {source_library_id}").format(
                    source_library_id=self.source_library_id
                ),
                status=400,
            )
        return Response()

    def sync_from_library(self, upgrade_to_latest: bool = False) -> None:
        """
        Synchronize children with source library.

        If `upgrade_to_latest==True` or if source library version is unset, update library version to latest.
        Otherwise, use current source library version.

        Raises ObjectDoesNotExist if library or version is missing.
        """
        self.get_tools(to_read_library_content=True).trigger_library_sync(
            dest_block=self,
            library_version=(None if upgrade_to_latest else self.source_library_version),
        )

    @XBlock.json_handler
    def is_v2_library(self, data, suffix=''):  # pylint: disable=unused-argument
        """
        Check the library version by library_id.

        This is a temporary handler needed for hiding the Problem Type xblock editor field for V2 libraries.
        """
        lib_key = data.get('library_key')
        try:
            LibraryLocatorV2.from_string(lib_key)
        except InvalidKeyError:
            is_v2 = False
        else:
            is_v2 = True
        return {'is_v2': is_v2}

    @XBlock.handler
    def children_are_syncing(self, request, suffix=''):  # pylint: disable=unused-argument
        """
        Returns whether this block is currently having its children updated from the source library.
        """
        try:
            is_updating = self.get_tools().are_children_syncing(self)
        except LibraryToolsUnavailable:
            is_updating = False
        return Response(json.dumps(is_updating))

    def studio_post_duplicate(self, store, source_block):
        """
        Used by the studio after basic duplication of a source block. We handle the children
        ourselves, because we have to properly reference the library upstream and set the overrides.

        Otherwise we'll end up losing data on the next refresh.
        """
        self._validate_sync_permissions()
        self.get_tools(to_read_library_content=True).trigger_duplication(source_block=source_block, dest_block=self)
        return True  # Children have been handled.

    def _validate_library_version(self, validation, lib_tools, version, library_key):
        """
        Validates library version
        """
        latest_version = lib_tools.get_latest_library_version(library_key)
        if latest_version is not None:
            if version is None or version != latest_version:
                validation.set_summary(
                    StudioValidationMessage(
                        StudioValidationMessage.WARNING,
                        _('This component is out of date. The library has new content.'),
                        # TODO: change this to action_runtime_event='...' once the unit page supports that feature.
                        # See https://openedx.atlassian.net/browse/TNL-993
                        action_class='library-update-btn',
                        # Translators: {refresh_icon} placeholder is substituted to "↻" (without double quotes)
                        action_label=_("{refresh_icon} Update now.").format(refresh_icon="↻")
                    )
                )
                return False
        else:
            validation.set_summary(
                StudioValidationMessage(
                    StudioValidationMessage.ERROR,
                    _('Library is invalid, corrupt, or has been deleted.'),
                    action_class='edit-button',
                    action_label=_("Edit Library List.")
                )
            )
            return False
        return True

    def _set_validation_error_if_empty(self, validation, summary):
        """  Helper method to only set validation summary if it's empty """
        if validation.empty:
            validation.set_summary(summary)

    def validate(self):
        """
        Validates the state of this Library Content Block Instance. This
        is the override of the general XBlock method, and it will also ask
        its superclass to validate.
        """
        validation = super().validate()
        if not isinstance(validation, StudioValidation):
            validation = StudioValidation.copy(validation)
        try:
            lib_tools = self.get_tools(to_read_library_content=True)
        except LibraryToolsUnavailable:
            validation.set_summary(
                StudioValidationMessage(
                    StudioValidationMessage.ERROR,
                    _(
                        "This course does not support content libraries. "
                        "Contact your system administrator for more information."
                    )
                )
            )
            return validation
        if not self.source_library_id:
            validation.set_summary(
                StudioValidationMessage(
                    StudioValidationMessage.NOT_CONFIGURED,
                    _("A library has not yet been selected."),
                    action_class='edit-button',
                    action_label=_("Select a Library.")
                )
            )
            return validation
        self._validate_library_version(validation, lib_tools, self.source_library_version, self.source_library_key)

        # Note: we assume children have been synced
        # since the last time fields like source_library_id or capa_types were changed.
        matching_children_count = len(self.children)  # pylint: disable=no-member
        if matching_children_count == 0:
            self._set_validation_error_if_empty(
                validation,
                StudioValidationMessage(
                    StudioValidationMessage.WARNING,
                    (gettext('There are no problems in the specified library of type {capa_type}.'))
                    .format(capa_type=self.capa_type),
                    action_class='edit-button',
                    action_label=_("Select another problem type.")
                )
            )

        if matching_children_count < self.max_count:
            self._set_validation_error_if_empty(
                validation,
                StudioValidationMessage(
                    StudioValidationMessage.WARNING,
                    (
                        ngettext(
                            'The specified library is configured to fetch {count} problem, ',
                            'The specified library is configured to fetch {count} problems, ',
                            self.max_count
                        ) +
                        ngettext(
                            'but there is only {actual} matching problem.',
                            'but there are only {actual} matching problems.',
                            matching_children_count
                        )
                    ).format(count=self.max_count, actual=matching_children_count),
                    action_class='edit-button',
                    action_label=_("Edit the library configuration.")
                )
            )

        return validation

    def source_library_values(self):
        """
        Return a list of possible values for self.source_library_id
        """
        lib_tools = self.get_tools()
        user_perms = self.runtime.service(self, 'studio_user_permissions')
        all_libraries = [
            (key, bleach.clean(name)) for key, name in lib_tools.list_available_libraries()
            if user_perms.can_read(key) or self.source_library_id == str(key)
        ]
        all_libraries.sort(key=lambda entry: entry[1])  # Sort by name
        if self.source_library_id and self.source_library_key not in [entry[0] for entry in all_libraries]:
            all_libraries.append((self.source_library_id, _("Invalid Library")))
        all_libraries = [("", _("No Library Selected"))] + all_libraries
        values = [{"display_name": name, "value": str(key)} for key, name in all_libraries]
        return values

    def post_editor_saved(self, user, old_metadata, old_content):  # pylint: disable=unused-argument
        """
        If source library, library version or capa_type have been edited, upgrade library,
        clear the candidates & sync automatically.

        TODO: capa_type doesn't really need to trigger an upgrade once we've migrated to V2.
        """
        source_lib_changed = (self.source_library_id != old_metadata.get("source_library_id", ""))
        capa_filter_changed = (self.capa_type != old_metadata.get("capa_type", ANY_CAPA_TYPE_VALUE))
        if source_lib_changed or capa_filter_changed:
            try:
                self.sync_from_library(upgrade_to_latest=True)
                self.candidates = []
            except (ObjectDoesNotExist, LibraryToolsUnavailable):
                # The validation area will display an error message, no need to do anything now.
                pass

    def has_dynamic_children(self):
        """
        Inform the runtime that our children vary per-user.
        See get_child_blocks()
        """
        return True

    def get_content_titles(self):
        """
        Returns list of friendly titles for our selected children only; without
        thi, all possible children's titles would be seen in the sequence bar in
        the LMS.

        This overwrites the get_content_titles method included in x_module by default.
        """
        titles = []
        for child in self.get_child_blocks():
            titles.extend(child.get_content_titles())
        return titles

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        """
        parses the definition and child objects from a piece of xml, the storage format for xblocks.
        """
        children = []

        for child in xml_object.getchildren():
            try:
                children.append(system.process_xml(etree.tostring(child)).scope_ids.usage_id)
            except (XMLSyntaxError, AttributeError):
                msg = (
                    "Unable to load child when parsing Library Content Block. "
                    "This can happen when a comment is manually added to the course export."
                )
                logger.error(msg)
                if system.error_tracker is not None:
                    system.error_tracker(msg)

        definition = dict(xml_object.attrib.items())
        return definition, children

    def definition_to_xml(self, resource_fs):
        """ Exports Library Content Block to XML """
        xml_object = etree.Element('library_content')
        for child in self.get_children():
            self.runtime.add_block_as_child_node(child, xml_object)
        # Set node attributes based on our fields.
        for field_name, field in self.fields.items():  # pylint: disable=no-member
            if field_name in ('children', 'parent', 'content'):
                continue
            if field.is_set_on(self):
                xml_object.set(field_name, str(field.read_from(self)))
        return xml_object


class LibrarySummary:
    """
    A library summary object which contains the fields required for library listing on studio.
    """

    def __init__(self, library_locator, display_name):
        """
        Initialize LibrarySummary

        Arguments:
        library_locator (LibraryLocator):  LibraryLocator object of the library.

        display_name (unicode): display name of the library.
        """
        self.display_name = display_name if display_name else _("Empty")

        self.id = library_locator  # pylint: disable=invalid-name
        self.location = library_locator.make_usage_key('library', 'library')

    @property
    def display_org_with_default(self):
        """
        Org display names are not implemented. This just provides API compatibility with CourseBlock.
        Always returns the raw 'org' field from the key.
        """
        return self.location.library_key.org

    @property
    def display_number_with_default(self):
        """
        Display numbers are not implemented. This just provides API compatibility with CourseBlock.
        Always returns the raw 'library' field from the key.
        """
        return self.location.library_key.library
