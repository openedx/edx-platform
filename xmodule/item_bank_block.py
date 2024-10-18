"""
Definitions for ItemBankMixin and ItemBankBlock.
"""
from __future__ import annotations

import json
import logging
import random
from copy import copy
from django.conf import settings
from django.utils.functional import classproperty
from lxml import etree
from lxml.etree import XMLSyntaxError
from rest_framework import status
from web_fragments.fragment import Fragment
from webob import Response
from xblock.completable import XBlockCompletionMode
from xblock.core import XBlock
from xblock.fields import Boolean, Integer, List, Scope, String

from xmodule.mako_block import MakoTemplateBlockBase
from xmodule.studio_editable import StudioEditableBlock
from xmodule.util.builtin_assets import add_webpack_js_to_fragment
from xmodule.validation import StudioValidation, StudioValidationMessage
from xmodule.xml_block import XmlMixin
from xmodule.x_module import (
    ResourceTemplates,
    XModuleMixin,
    XModuleToXBlockMixin,
    shim_xmodule_js,
    STUDENT_VIEW,
)

_ = lambda text: text

logger = logging.getLogger(__name__)


@XBlock.needs('mako')
@XBlock.wants('user')
class ItemBankMixin(
    # @@TODO do we really need all these mixins?
    MakoTemplateBlockBase,
    XmlMixin,
    XModuleToXBlockMixin,
    ResourceTemplates,
    XModuleMixin,
    StudioEditableBlock,
):
    """
    Shared logic for XBlock types which shows a random subset of their children to each learner.

    Concretely, this is the shared base for ItemBankBlock and LegacyLibraryContentBlock.
    Sharing fields and selection logic between those two blocks will allow us to eventually migrate
    LegacyLibraryContentBlocks (backed by V1 libraries) into ItemBankBlocks (backed by V2 libraries).
    """
    has_children = True
    has_author_view = True
    show_in_read_only_mode = True
    resources_dir = 'assets/library_content'
    mako_template = 'widgets/metadata-edit.html'
    studio_js_module_name = "VerticalDescriptor"

    max_count = Integer(
        display_name=_("Count"),
        help=_("Enter the number of components to display to each student. Set it to -1 to display all components."),
        default=1,
        scope=Scope.settings,
    )
    selected = List(
        # This is a list of (block_type, block_id) tuples used to record
        # which random/first set of matching blocks was selected per user
        default=[],
        scope=Scope.user_state,
    )
    # This cannot be called `show_reset_button`, because children blocks inherit this as a default value.
    allow_resetting_children = Boolean(
        display_name=_("Show Reset Button"),
        help=_("Determines whether a 'Reset Problems' button is shown, so users may reset their answers and reshuffle "
               "selected items."),
        scope=Scope.settings,
        default=False
    )

    @classproperty
    def completion_mode(cls):  # pylint: disable=no-self-argument
        """
        Allow overriding the completion mode with a feature flag.

        This is a property, so it can be dynamically overridden in tests, as it is not evaluated at runtime.
        """
        if settings.FEATURES.get('MARK_LIBRARY_CONTENT_BLOCK_COMPLETE_ON_VIEW', False):
            return XBlockCompletionMode.COMPLETABLE

        return XBlockCompletionMode.AGGREGATOR

    @classmethod
    def make_selection(cls, selected, children, max_count):
        """
        Dynamically selects block_ids indicating which of the possible children are displayed to the current user.

        Arguments:
            selected - list of (block_type, block_id) tuples assigned to this student
            children - children of this block
            max_count - number of components to display to each student

        Returns:
            A dict containing the following keys:

            'selected' (set) of (block_type, block_id) tuples assigned to this student
            'invalid' (set) of dropped (block_type, block_id) tuples that are no longer valid
            'overlimit' (set) of dropped (block_type, block_id) tuples that were previously selected
            'added' (set) of newly added (block_type, block_id) tuples
        """
        rand = random.Random()

        selected_keys = {tuple(k) for k in selected}  # set of (block_type, block_id) tuples assigned to this student

        # Determine which of our children we will show:
        valid_block_keys = {(c.block_type, c.block_id) for c in children}

        # Remove any selected blocks that are no longer valid:
        invalid_block_keys = (selected_keys - valid_block_keys)
        if invalid_block_keys:
            selected_keys -= invalid_block_keys

        # If max_count has been decreased, we may have to drop some previously selected blocks:
        overlimit_block_keys = set()
        if len(selected_keys) > max_count:
            num_to_remove = len(selected_keys) - max_count
            overlimit_block_keys = set(rand.sample(list(selected_keys), num_to_remove))
            selected_keys -= overlimit_block_keys

        # Do we have enough blocks now?
        num_to_add = max_count - len(selected_keys)

        added_block_keys = None
        if num_to_add > 0:
            # We need to select [more] blocks to display to this user:
            pool = valid_block_keys - selected_keys
            num_to_add = min(len(pool), num_to_add)
            added_block_keys = set(rand.sample(list(pool), num_to_add))
            selected_keys |= added_block_keys

        if any((invalid_block_keys, overlimit_block_keys, added_block_keys)):
            selected = list(selected_keys)
            random.shuffle(selected)

        return {
            'selected': selected,
            'invalid': invalid_block_keys,
            'overlimit': overlimit_block_keys,
            'added': added_block_keys,
        }

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

        block_keys = self.make_selection(self.selected, self.children, max_count)  # pylint: disable=no-member

        self.publish_selected_children_events(
            block_keys,
            self.format_block_keys_for_analytics,
            self._publish_event,
        )

        if any(block_keys[changed] for changed in ('invalid', 'overlimit', 'added')):
            # Save our selections to the user state, to ensure consistency:
            selected = block_keys['selected']
            self.selected = selected  # TODO: this doesn't save from the LMS "Progress" page.

        return self.selected

    def format_block_keys_for_analytics(self, block_keys: list[tuple[str, str]]) -> list[dict]:
        """
        Given a list of (block_type, block_id) pairs, prepare the JSON-ready metadata needed for analytics logging.

        This is [
            {"usage_key": x, "original_usage_key": y, "original_usage_version": z, "descendants": [...]}
        ]
        where the main list contains all top-level blocks, and descendants contains a *flat* list of all
        descendants of the top level blocks, if any.

        Must be implemented in child class.

        @@TODO: Do we actually want to share this format between ItemBankBlocks and LegacyLibraryContentBlocks?
                Or should we define a fresh format for ItemBankBlocks?
        """
        raise NotImplementedError

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

    def studio_view(self, _context):
        """
        Return the studio view.
        """
        fragment = Fragment(
            self.runtime.service(self, 'mako').render_cms_template(self.mako_template, self.get_context())
        )
        add_webpack_js_to_fragment(fragment, 'LibraryContentBlockEditor')
        shim_xmodule_js(fragment, self.studio_js_module_name)
        return fragment

    def get_child_blocks(self):
        """
        Return only the subset of our children relevant to the current student.
        """
        return list(self._get_selected_child_blocks())

    def get_user_id(self):
        """
        Get the ID of the current user.
        """
        user_service = self.runtime.service(self, 'user')
        if user_service:
            user_id = user_service.get_current_user().opt_attrs.get('edx-platform.user_id', None)
        else:
            user_id = None
        return user_id

    def has_dynamic_children(self):
        """
        Inform the runtime that our children vary per-user.
        See get_child_blocks() above
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
        @@TODO docstring
        """
        children = []

        for child in xml_object.getchildren():
            try:
                children.append(system.process_xml(etree.tostring(child)).scope_ids.usage_id)
            except (XMLSyntaxError, AttributeError):
                msg = (
                    "Unable to load child when parsing {self.usage_key.block_type} Block. "
                    "This can happen when a comment is manually added to the course export."
                )
                logger.error(msg)
                if system.error_tracker is not None:
                    system.error_tracker(msg)

        definition = dict(xml_object.attrib.items())
        return definition, children

    def definition_to_xml(self, resource_fs):
        """ Exports ItemBankBlock to XML """
        xml_object = etree.Element(self.usage_key.block_type)
        for child in self.get_children():
            self.runtime.add_block_as_child_node(child, xml_object)
        # Set node attributes based on our fields.
        for field_name, field in self.fields.items():  # pylint: disable=no-member
            if field_name in ('children', 'parent', 'content'):
                continue
            if field.is_set_on(self):
                xml_object.set(field_name, str(field.read_from(self)))
        return xml_object


class ItemBankBlock(ItemBankMixin, XBlock):
    """
    An XBlock which shows a random subset of its children to each learner.

    Unlike LegacyLibraryContentBlock, this block does not need to worry about synchronization, capa_type filtering, etc.
    That is all implemented using `upstream` links on each individual child.
    """
    display_name = String(
        display_name=_("Display Name"),
        help=_("The display name for this component."),
        default="Problem Bank",
        scope=Scope.settings,
    )

    def validate(self):
        """
        Validates the state of this ItemBankBlock Instance.

        @@TODO implement
        """
        validation = super().validate()
        if not isinstance(validation, StudioValidation):
            validation = StudioValidation.copy(validation)
        if not validation.empty:
            pass  # If there's already a validation error, leave it there.
        elif not self.children:
           validation.set_summary(
                StudioValidationMessage(
                    StudioValidationMessage.WARNING,
                    (_('No problems have been selected.')),
                    action_class='edit-button',
                    action_label=_("Select problems to randomize.")
                )
            )
        elif len(self.children) < self.max_count:
           validation.set_summary(
                StudioValidationMessage(
                    StudioValidationMessage.WARNING,
                    _(
                        "The problem bank has been configured to show {count} problems, "
                        "but only {actual} have been selected."
                    ).format(count=self.max_count, actual=len(self.children)),
                    action_class='edit-button',
                    action_label=_("Edit the problem bank configuration.")
                )
            )
        return validation

    def author_view(self, context):
        """
        Renders the Studio views.
        Normal studio view: If block is properly configured, displays library status summary
        Studio container view: displays a preview of all possible children.
        """
        fragment = Fragment()
        root_xblock = context.get('root_xblock')
        is_root = root_xblock and root_xblock.location == self.location
        # User has clicked the "View" link. Show a preview of all possible children:
        if self.children:  # pylint: disable=no-member
            max_count = self.max_count
            if max_count < 0:
                max_count = len(self.children)
            context['can_edit_visibility'] = False
            context['can_move'] = False
            context['can_collapse'] = True
            self.render_children(context, fragment, can_reorder=False, can_add=False)
        context['is_loading'] = False

        fragment.initialize_js('LibraryContentAuthorView')
        return fragment

    def format_block_keys_for_analytics(self, block_keys: list[tuple[str, str]]) -> list[dict]:
        """
        Implement format_block_keys_for_analytics using the `upstream` link system.

        @@TODO this doesn't include original_usage_key, original_usage_version, or descendends!
        """
        return [{"usage_key": str(self.context_key.make_usage_key(*block_key))} for block_key in block_keys]
