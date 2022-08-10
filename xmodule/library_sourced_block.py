"""
Library Sourced Content XBlock
"""
import json
import logging
from copy import copy

import bleach
from lazy import lazy
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import LibraryLocator, LibraryLocatorV2
from pkg_resources import resource_string
from web_fragments.fragment import Fragment
from webob import Response
from xblock.core import XBlock
from xblock.fields import List, Scope, String
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin

from xmodule.mako_module import MakoTemplateBlockBase
from xmodule.studio_editable import StudioEditableBlock as EditableChildrenMixin
from xmodule.util.xmodule_django import add_webpack_to_fragment
from xmodule.validation import StudioValidation, StudioValidationMessage
from xmodule.x_module import (
    STUDENT_VIEW,
    HTMLSnippet,
    ResourceTemplates,
    XModuleMixin,
    XModuleToXBlockMixin,
    shim_xmodule_js
)

log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)

# Make '_' a no-op so we can scrape strings. Using lambda instead of
#  `django.utils.translation.ugettext_noop` because Django cannot be imported in this file
_ = lambda text: text


@XBlock.wants('library_tools')  # Only needed in studio
@XBlock.wants('studio_user_permissions')  # Only available in studio
class LibrarySourcedBlock(
    StudioEditableXBlockMixin,
    MakoTemplateBlockBase,
    XModuleToXBlockMixin,
    HTMLSnippet,
    ResourceTemplates,
    XModuleMixin,
    EditableChildrenMixin,
):
    """
    Library Sourced Content XBlock

    Allows copying specific XBlocks from a Blockstore-based content library into
    a modulestore-based course. The selected blocks are copied and become
    children of this block.

    When we implement support for Blockstore-based courses, it's expected we'll
    use a different mechanism for importing library content into a course.
    """
    display_name = String(
        help=_("The display name for this component."),
        default="Library Reference Block",
        display_name=_("Display Name"),
        scope=Scope.content,
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
    source_block_ids = List(
        display_name=_("Library Blocks List"),
        help=_("Enter the IDs of the library XBlocks that you wish to use."),
        scope=Scope.content,
    )
    editable_fields = ("source_block_ids",)
    has_children = True
    has_author_view = True

    resources_dir = 'assets/library_source_block'

    preview_view_js = {
        'js': [],
        'xmodule_js': resource_string(__name__, 'js/src/xmodule.js'),
    }
    preview_view_css = {
        'scss': [],
    }

    mako_template = 'widgets/metadata-edit.html'
    studio_js_module_name = "VerticalDescriptor"
    studio_view_js = {
        'js': [
            resource_string(__name__, 'js/src/vertical/edit.js'),
        ],
        'xmodule_js': resource_string(__name__, 'js/src/xmodule.js'),
    }
    studio_view_css = {
        'scss': [],
    }

    def __str__(self):
        return f"LibrarySourcedBlock: {self.display_name}"

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
            context['is_selected'] = str(child.location) in self.source_block_ids
            rendered_child = child.render(EditableChildrenMixin.get_preview_view_name(child), context)
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

    def studio_view(self, _context):
        """
        Return the studio view.
        """
        fragment = Fragment(
            self.runtime.service(self, 'mako').render_template(self.mako_template, self.get_context())
        )
        add_webpack_to_fragment(fragment, 'LibrarySourcedBlockStudio')
        shim_xmodule_js(fragment, self.studio_js_module_name)

        return fragment

    def author_view(self, context):
        """
        Renders the Studio preview view.
        """
        fragment = Fragment()
        root_xblock = context.get('root_xblock')
        is_root = root_xblock and root_xblock.location == self.location  # pylint: disable=no-member
        # If block ID is not defined, ask user for the component ID in the author_view itself.
        # We don't display the editor if is_root as that page should represent the student_view without any ambiguity
        is_loading = self.tools.is_loading(self.location)
        if is_root and not is_loading:
            context = {} if not context else copy(context)  # Isolate context - without this there are weird
            # bugs in Studio EditableChildrenMixin.render_children will render HTML that allows instructors
            # to make edits to the children
            context['can_move'] = False
            context['selectable'] = True
            context['can_collapse'] = True
            self.render_children(context, fragment, can_reorder=False, can_add=False)
            return fragment
        context['is_loading'] = is_loading
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/library_source_edit.js'))
        fragment.initialize_js('LibrarySourceAuthorView')
        return fragment

    def _get_selected_child_blocks(self):
        """
        Generator returning XBlock instances of the children selected for the
        current user.
        """
        for block_id in self.source_block_ids:
            usage_key = UsageKey.from_string(block_id)
            yield self.runtime.get_block(usage_key)

    def student_view(self, context):
        """
        Renders the view that learners see.
        """
        fragment = Fragment()
        child_context = {} if not context else copy(context)

        fragment.add_content('<div class="library-sourced-content">')
        for child in self._get_selected_child_blocks():
            if child is None:
                # TODO: Fix the underlying issue in TNL-7424
                # This shouldn't be happening, but does for an as-of-now
                # unknown reason. Until we address the underlying issue,
                # let's at least log the error explicitly, ignore the
                # exception, and prevent the page from resulting in a
                # 500-response.
                log.error('Skipping display for child block that is None')
                continue
            for displayable in child.displayable_items():
                rendered_child = displayable.render(STUDENT_VIEW, child_context)
                fragment.add_content(rendered_child.content)
                fragment.add_fragment_resources(rendered_child)

        fragment.add_content('</div>')
        return fragment

    def _validate_library_version(self, validation, lib_tools, version, library_key):
        """
        Validates library version
        """
        latest_version = lib_tools.get_library_version(library_key)
        if latest_version is not None:
            if version is None or version != str(latest_version):
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
        """
        Helper method to only set validation summary if it's empty
        """
        if validation.empty:
            validation.set_summary(summary)

    def validate(self):
        """
        Validates the state of this library_sourced_xblock Instance. This is the override of the general XBlock method,
        and it will also ask its superclass to validate.
        """
        validation = super().validate()
        validation = StudioValidation.copy(validation)

        if not self.source_library_id:
            validation.set_summary(
                StudioValidationMessage(
                    StudioValidationMessage.NOT_CONFIGURED,
                    _("A library has not been selected yet."),
                    action_class='edit-button',
                    action_label=_("Select a Library.")
                )
            )
            return validation

        if not self.children:
            validation.set_summary(
                StudioValidationMessage(
                    StudioValidationMessage.NOT_CONFIGURED,
                    _("There are no problem types in the specified libraries."),
                    action_class='edit-button',
                    action_label=_("Select another Library.")
                )
            )
            return validation

        self._validate_library_version(validation, self.tools, self.source_library_version, self.source_library_key)
        return validation

    def source_library_values(self):
        """
        Return a list of possible values for self.source_library_id
        """
        user_perms = self.runtime.service(self, 'studio_user_permissions')
        all_libraries = [
            (key, bleach.clean(name)) for key, name in self.tools.list_available_libraries()
            if user_perms.can_read(key) or self.source_library_id == str(key)
        ]
        all_libraries.sort(key=lambda entry: entry[1])  # Sort by name
        if self.source_library_id and self.source_library_key not in [entry[0] for entry in all_libraries]:
            all_libraries.append((self.source_library_id, _("Invalid Library")))
        all_libraries = [("", _("No Library Selected"))] + all_libraries
        values = [{"display_name": name, "value": str(key)} for key, name in all_libraries]
        return values

    @property
    def non_editable_metadata_fields(self):
        non_editable_fields = super().non_editable_metadata_fields
        non_editable_fields.extend([
            LibrarySourcedBlock.source_block_ids,
            LibrarySourcedBlock.source_library_version,
        ])
        return non_editable_fields

    @property
    def source_library_key(self):
        """
        Convenience method to get the library ID as a LibraryLocator and not just a string
        """
        try:
            return LibraryLocator.from_string(self.source_library_id)
        except InvalidKeyError:
            return LibraryLocatorV2.from_string(self.source_library_id)

    @lazy
    def tools(self):
        """
        Grab the library tools service or raise an error.
        """
        return self.runtime.service(self, 'library_tools')

    def editor_saved(self, user, old_metadata, old_content):  # lint-amnesty, pylint: disable=unused-argument
        """
        If source_library_id is empty, clear source_library_version and children.
        """
        if not self.source_library_id:
            self.children = []  # lint-amnesty, pylint: disable=attribute-defined-outside-init
            self.source_library_version = ""
        else:
            self.source_library_version = str(self.tools.get_library_version(self.source_library_id))

    def post_editor_saved(self):  # lint-amnesty, pylint: disable=unused-argument
        """
        If source_library_id has been edited, refresh_children automatically.
        """
        try:
            if self.source_library_id:
                self.refresh_children()
        except ValueError:
            pass  # The validation area will display an error message, no need to do anything now.

    @XBlock.handler
    def refresh_children(self, request=None, suffix=None):  # lint-amnesty, pylint: disable=unused-argument
        """
        Refresh children:
        This method is to be used when any of the libraries that this block
        references have been updated. It will re-fetch all matching blocks from
        the libraries, and copy them as children of this block. The children
        will be given new block_ids, but the definition ID used should be the
        exact same definition ID used in the library.

        This method will update this block's 'source_library_id' field to store
        the version number of the libraries used, so we easily determine if
        this block is up to date or not.
        """
        user_perms = self.runtime.service(self, 'studio_user_permissions')
        if not self.tools:
            return Response("Library Tools unavailable in current runtime.", status=400)
        self.tools.update_children(self, user_perms)
        return Response()

    @XBlock.handler
    def get_block_ids(self, request, suffix=''):  # lint-amnesty, pylint: disable=unused-argument
        """
        Return source_block_ids.
        """
        return Response(json.dumps({'source_block_ids': self.source_block_ids}))

    @XBlock.handler
    def get_import_task_status(self, request, suffix=''):  # lint-amnesty, pylint: disable=unused-argument
        """
        Return task status for update_children_task.
        """
        status = self.tools.import_task_status(self.location)
        return Response(json.dumps({'status': status}))
