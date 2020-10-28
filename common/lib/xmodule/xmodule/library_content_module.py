# -*- coding: utf-8 -*-
"""
LibraryContent: The XBlock used to include blocks from a library in a course.
"""


import json
import logging
import random
from copy import copy
from gettext import ngettext

import six
import bleach
from lazy import lazy
from lxml import etree
from opaque_keys.edx.locator import LibraryLocator
from pkg_resources import resource_string
from six import text_type
from six.moves import zip
from web_fragments.fragment import Fragment
from webob import Response
from xblock.completable import XBlockCompletionMode
from xblock.core import XBlock
from xblock.fields import Integer, List, Scope, String

from capa.responsetypes import registry
from xmodule.mako_module import MakoTemplateBlockBase
from xmodule.studio_editable import StudioEditableBlock
from xmodule.util.xmodule_django import add_webpack_to_fragment
from xmodule.validation import StudioValidation, StudioValidationMessage
from xmodule.xml_module import XmlMixin
from xmodule.x_module import (
    HTMLSnippet,
    ResourceTemplates,
    shim_xmodule_js,
    STUDENT_VIEW,
    XModuleMixin,
    XModuleDescriptorToXBlockMixin,
    XModuleToXBlockMixin,
)


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


@XBlock.wants('library_tools')  # Only needed in studio
@XBlock.wants('studio_user_permissions')  # Only available in studio
@XBlock.wants('user')
class LibraryContentBlock(
    MakoTemplateBlockBase,
    XmlMixin,
    XModuleDescriptorToXBlockMixin,
    XModuleToXBlockMixin,
    HTMLSnippet,
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
    has_children = True
    has_author_view = True

    resources_dir = 'assets/library_content'

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

    show_in_read_only_mode = True

    completion_mode = XBlockCompletionMode.AGGREGATOR

    display_name = String(
        display_name=_("Display Name"),
        help=_("The display name for this component."),
        default="Randomized Content Block",
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
    mode = String(
        display_name=_("Mode"),
        help=_("Determines how content is drawn from the library"),
        default="random",
        values=[
            {"display_name": _("Choose n at random"), "value": "random"}
            # Future addition: Choose a new random set of n every time the student refreshes the block, for self tests
            # Future addition: manually selected blocks
        ],
        scope=Scope.settings,
    )
    max_count = Integer(
        display_name=_("Count"),
        help=_("Enter the number of components to display to each student."),
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
    selected = List(
        # This is a list of (block_type, block_id) tuples used to record
        # which random/first set of matching blocks was selected per user
        default=[],
        scope=Scope.user_state,
    )

    @property
    def source_library_key(self):
        """
        Convenience method to get the library ID as a LibraryLocator and not just a string
        """
        return LibraryLocator.from_string(self.source_library_id)

    @classmethod
    def make_selection(cls, selected, children, max_count, mode):
        """
        Dynamically selects block_ids indicating which of the possible children are displayed to the current user.

        Arguments:
            selected - list of (block_type, block_id) tuples assigned to this student
            children - children of this block
            max_count - number of components to display to each student
            mode - how content is drawn from the library

        Returns:
            A dict containing the following keys:

            'selected' (set) of (block_type, block_id) tuples assigned to this student
            'invalid' (set) of dropped (block_type, block_id) tuples that are no longer valid
            'overlimit' (set) of dropped (block_type, block_id) tuples that were previously selected
            'added' (set) of newly added (block_type, block_id) tuples
        """
        rand = random.Random()

        selected_keys = set(tuple(k) for k in selected)  # set of (block_type, block_id) tuples assigned to this student

        # Determine which of our children we will show:
        valid_block_keys = set((c.block_type, c.block_id) for c in children)

        # Remove any selected blocks that are no longer valid:
        invalid_block_keys = (selected_keys - valid_block_keys)
        if invalid_block_keys:
            selected_keys -= invalid_block_keys

        # If max_count has been decreased, we may have to drop some previously selected blocks:
        overlimit_block_keys = set()
        if len(selected_keys) > max_count:
            num_to_remove = len(selected_keys) - max_count
            overlimit_block_keys = set(rand.sample(selected_keys, num_to_remove))
            selected_keys -= overlimit_block_keys

        # Do we have enough blocks now?
        num_to_add = max_count - len(selected_keys)

        added_block_keys = None
        if num_to_add > 0:
            # We need to select [more] blocks to display to this user:
            pool = valid_block_keys - selected_keys
            if mode == "random":
                num_to_add = min(len(pool), num_to_add)
                added_block_keys = set(rand.sample(pool, num_to_add))
                # We now have the correct n random children to show for this user.
            else:
                raise NotImplementedError("Unsupported mode.")
            selected_keys |= added_block_keys

        if any([invalid_block_keys, overlimit_block_keys, added_block_keys]):
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
            "location": six.text_type(self.location),
            "result": result,
            "previous_count": getattr(self, "_last_event_result_count", len(self.selected)),
            "max_count": self.max_count,
        }
        event_data.update(kwargs)
        self.runtime.publish(self, "edx.librarycontentblock.content.{}".format(event_name), event_data)
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
        Returns a list() of block_ids indicating which of the possible children
        have been selected to display to the current user.

        This reads and updates the "selected" field, which has user_state scope.

        Note: the return value (self.selected) contains block_ids. To get
        actual BlockUsageLocators, it is necessary to use self.children,
        because the block_ids alone do not specify the block type.
        """
        block_keys = self.make_selection(self.selected, self.children, self.max_count, "random")  # pylint: disable=no-member

        # Publish events for analytics purposes:
        lib_tools = self.runtime.service(self, 'library_tools')
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

    def _get_selected_child_blocks(self):
        """
        Generator returning XBlock instances of the children selected for the
        current user.
        """
        for block_type, block_id in self.selected_children():
            yield self.runtime.get_block(self.location.course_key.make_usage_key(block_type, block_id))

    def student_view(self, context):
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
            for displayable in child.displayable_items():
                rendered_child = displayable.render(STUDENT_VIEW, child_context)
                fragment.add_fragment_resources(rendered_child)
                contents.append({
                    'id': text_type(displayable.location),
                    'content': rendered_child.content,
                })

        fragment.add_content(self.system.render_template('vert_module.html', {
            'items': contents,
            'xblock_context': context,
            'show_bookmark_button': False,
            'watched_completable_blocks': set(),
            'completion_delay_ms': None,
        }))
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

        if is_root:
            # User has clicked the "View" link. Show a preview of all possible children:
            if self.children:  # pylint: disable=no-member
                fragment.add_content(self.system.render_template("library-block-author-preview-header.html", {
                    'max_count': self.max_count,
                    'display_name': self.display_name or self.url_name,
                }))
                context['can_edit_visibility'] = False
                context['can_move'] = False
                self.render_children(context, fragment, can_reorder=False, can_add=False)
        # else: When shown on a unit page, don't show any sort of preview -
        # just the status of this block in the validation area.

        # The following JS is used to make the "Update now" button work on the unit page and the container view:
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/library_content_edit.js'))
        fragment.initialize_js('LibraryContentAuthorView')
        return fragment

    def studio_view(self, _context):
        """
        Return the studio view.
        """
        fragment = Fragment(
            self.system.render_template(self.mako_template, self.get_context())
        )
        add_webpack_to_fragment(fragment, 'LibraryContentBlockStudio')
        shim_xmodule_js(fragment, self.studio_js_module_name)
        return fragment

    def get_child_descriptors(self):
        """
        Return only the subset of our children relevant to the current student.
        """
        return list(self._get_selected_child_blocks())

    @property
    def non_editable_metadata_fields(self):
        non_editable_fields = super().non_editable_metadata_fields
        # The only supported mode is currently 'random'.
        # Add the mode field to non_editable_metadata_fields so that it doesn't
        # render in the edit form.
        non_editable_fields.extend([
            LibraryContentBlock.mode,
            LibraryContentBlock.source_library_version,
        ])
        return non_editable_fields

    @lazy
    def tools(self):
        """
        Grab the library tools service or raise an error.
        """
        return self.runtime.service(self, 'library_tools')

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

    @XBlock.handler
    def refresh_children(self, request=None, suffix=None):
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

    # Copy over any overridden settings the course author may have applied to the blocks.
    def _copy_overrides(self, store, user_id, source, dest):
        """
        Copy any overrides the user has made on blocks in this library.
        """
        for field in six.itervalues(source.fields):
            if field.scope == Scope.settings and field.is_set_on(source):
                setattr(dest, field.name, field.read_from(source))
        if source.has_children:
            source_children = [self.runtime.get_block(source_key) for source_key in source.children]
            dest_children = [self.runtime.get_block(dest_key) for dest_key in dest.children]
            for source_child, dest_child in zip(source_children, dest_children):
                self._copy_overrides(store, user_id, source_child, dest_child)
        store.update_item(dest, user_id)

    def studio_post_duplicate(self, store, source_block):
        """
        Used by the studio after basic duplication of a source block. We handle the children
        ourselves, because we have to properly reference the library upstream and set the overrides.

        Otherwise we'll end up losing data on the next refresh.
        """
        # The first task will be to refresh our copy of the library to generate the children.
        # We must do this at the currently set version of the library block. Otherwise we may not have
        # exactly the same children-- someone may be duplicating an out of date block, after all.
        user_id = self.get_user_id()
        user_perms = self.runtime.service(self, 'studio_user_permissions')
        if not self.tools:
            raise RuntimeError("Library tools unavailable, duplication will not be sane!")
        self.tools.update_children(self, user_perms, version=self.source_library_version)

        self._copy_overrides(store, user_id, source_block, self)

        # Children have been handled.
        return True

    def _validate_library_version(self, validation, lib_tools, version, library_key):
        """
        Validates library version
        """
        latest_version = lib_tools.get_library_version(library_key)
        if latest_version is not None:
            if version is None or version != six.text_type(latest_version):
                validation.set_summary(
                    StudioValidationMessage(
                        StudioValidationMessage.WARNING,
                        _(u'This component is out of date. The library has new content.'),
                        # TODO: change this to action_runtime_event='...' once the unit page supports that feature.
                        # See https://openedx.atlassian.net/browse/TNL-993
                        action_class='library-update-btn',
                        # Translators: {refresh_icon} placeholder is substituted to "↻" (without double quotes)
                        action_label=_(u"{refresh_icon} Update now.").format(refresh_icon=u"↻")
                    )
                )
                return False
        else:
            validation.set_summary(
                StudioValidationMessage(
                    StudioValidationMessage.ERROR,
                    _(u'Library is invalid, corrupt, or has been deleted.'),
                    action_class='edit-button',
                    action_label=_(u"Edit Library List.")
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
        Validates the state of this Library Content Module Instance. This
        is the override of the general XBlock method, and it will also ask
        its superclass to validate.
        """
        validation = super().validate()
        if not isinstance(validation, StudioValidation):
            validation = StudioValidation.copy(validation)
        library_tools = self.runtime.service(self, "library_tools")
        if not (library_tools and library_tools.can_use_library_content(self)):
            validation.set_summary(
                StudioValidationMessage(
                    StudioValidationMessage.ERROR,
                    _(
                        u"This course does not support content libraries. "
                        u"Contact your system administrator for more information."
                    )
                )
            )
            return validation
        if not self.source_library_id:
            validation.set_summary(
                StudioValidationMessage(
                    StudioValidationMessage.NOT_CONFIGURED,
                    _(u"A library has not yet been selected."),
                    action_class='edit-button',
                    action_label=_(u"Select a Library.")
                )
            )
            return validation
        lib_tools = self.runtime.service(self, 'library_tools')
        self._validate_library_version(validation, lib_tools, self.source_library_version, self.source_library_key)

        # Note: we assume refresh_children() has been called
        # since the last time fields like source_library_id or capa_types were changed.
        matching_children_count = len(self.children)  # pylint: disable=no-member
        if matching_children_count == 0:
            self._set_validation_error_if_empty(
                validation,
                StudioValidationMessage(
                    StudioValidationMessage.WARNING,
                    _(u'There are no matching problem types in the specified libraries.'),
                    action_class='edit-button',
                    action_label=_(u"Select another problem type.")
                )
            )

        if matching_children_count < self.max_count:
            self._set_validation_error_if_empty(
                validation,
                StudioValidationMessage(
                    StudioValidationMessage.WARNING,
                    (
                        ngettext(
                            u'The specified library is configured to fetch {count} problem, ',
                            u'The specified library is configured to fetch {count} problems, ',
                            self.max_count
                        ) +
                        ngettext(
                            u'but there is only {actual} matching problem.',
                            u'but there are only {actual} matching problems.',
                            matching_children_count
                        )
                    ).format(count=self.max_count, actual=matching_children_count),
                    action_class='edit-button',
                    action_label=_(u"Edit the library configuration.")
                )
            )

        return validation

    def source_library_values(self):
        """
        Return a list of possible values for self.source_library_id
        """
        lib_tools = self.runtime.service(self, 'library_tools')
        user_perms = self.runtime.service(self, 'studio_user_permissions')
        all_libraries = [
            (key, bleach.clean(name)) for key, name in lib_tools.list_available_libraries()
            if user_perms.can_read(key) or self.source_library_id == six.text_type(key)
        ]
        all_libraries.sort(key=lambda entry: entry[1])  # Sort by name
        if self.source_library_id and self.source_library_key not in [entry[0] for entry in all_libraries]:
            all_libraries.append((self.source_library_id, _(u"Invalid Library")))
        all_libraries = [(u"", _("No Library Selected"))] + all_libraries
        values = [{"display_name": name, "value": six.text_type(key)} for key, name in all_libraries]
        return values

    def editor_saved(self, user, old_metadata, old_content):
        """
        If source_library_id or capa_type has been edited, refresh_children automatically.
        """
        old_source_library_id = old_metadata.get('source_library_id', [])
        if (old_source_library_id != self.source_library_id or
                old_metadata.get('capa_type', ANY_CAPA_TYPE_VALUE) != self.capa_type):
            try:
                self.refresh_children()
            except ValueError:
                pass  # The validation area will display an error message, no need to do anything now.

    def has_dynamic_children(self):
        """
        Inform the runtime that our children vary per-user.
        See get_child_descriptors() above
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
        for child in self.get_child_descriptors():
            titles.extend(child.get_content_titles())
        return titles

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        children = [
            system.process_xml(etree.tostring(child)).scope_ids.usage_id
            for child in xml_object.getchildren()
        ]
        definition = {
            attr_name: json.loads(attr_value)
            for attr_name, attr_value in xml_object.attrib.items()
        }
        return definition, children

    def definition_to_xml(self, resource_fs):
        """ Exports Library Content Module to XML """
        xml_object = etree.Element('library_content')
        for child in self.get_children():
            self.runtime.add_block_as_child_node(child, xml_object)
        # Set node attributes based on our fields.
        for field_name, field in six.iteritems(self.fields):
            if field_name in ('children', 'parent', 'content'):
                continue
            if field.is_set_on(self):
                xml_object.set(field_name, six.text_type(field.read_from(self)))
        return xml_object


class LibrarySummary(object):
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
        self.display_name = display_name if display_name else _(u"Empty")

        self.id = library_locator  # pylint: disable=invalid-name
        self.location = library_locator.make_usage_key('library', 'library')

    @property
    def display_org_with_default(self):
        """
        Org display names are not implemented. This just provides API compatibility with CourseDescriptor.
        Always returns the raw 'org' field from the key.
        """
        return self.location.library_key.org

    @property
    def display_number_with_default(self):
        """
        Display numbers are not implemented. This just provides API compatibility with CourseDescriptor.
        Always returns the raw 'library' field from the key.
        """
        return self.location.library_key.library
