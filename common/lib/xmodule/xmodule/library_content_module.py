# -*- coding: utf-8 -*-
"""
LibraryContent: The XBlock used to include blocks from a library in a course.
"""
import json
from lxml import etree
from copy import copy
from capa.responsetypes import registry
from gettext import ngettext
from lazy import lazy

from .mako_module import MakoModuleDescriptor
from opaque_keys.edx.locator import LibraryLocator
import random
from webob import Response
from xblock.core import XBlock
from xblock.fields import Scope, String, List, Integer, Boolean
from xblock.fragment import Fragment
from xmodule.validation import StudioValidationMessage, StudioValidation
from xmodule.x_module import XModule, STUDENT_VIEW
from xmodule.studio_editable import StudioEditableModule, StudioEditableDescriptor
from .xml_module import XmlDescriptor
from pkg_resources import resource_string  # pylint: disable=no-name-in-module


# Make '_' a no-op so we can scrape strings
_ = lambda text: text


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


class LibraryContentFields(object):
    """
    Fields for the LibraryContentModule.

    Separated out for now because they need to be added to the module and the
    descriptor.
    """
    # Please note the display_name of each field below is used in
    # common/test/acceptance/pages/studio/library.py:StudioLibraryContentXBlockEditModal
    # to locate input elements - keep synchronized
    display_name = String(
        display_name=_("Display Name"),
        help=_("Display name for this module"),
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
    filters = String(default="")  # TBD
    has_score = Boolean(
        display_name=_("Scored"),
        help=_("Set this value to True if this module is either a graded assignment or a practice problem."),
        default=False,
        scope=Scope.settings,
    )
    selected = List(
        # This is a list of (block_type, block_id) tuples used to record
        # which random/first set of matching blocks was selected per user
        default=[],
        scope=Scope.user_state,
    )
    has_children = True

    @property
    def source_library_key(self):
        """
        Convenience method to get the library ID as a LibraryLocator and not just a string
        """
        return LibraryLocator.from_string(self.source_library_id)


#pylint: disable=abstract-method
@XBlock.wants('library_tools')  # Only needed in studio
class LibraryContentModule(LibraryContentFields, XModule, StudioEditableModule):
    """
    An XBlock whose children are chosen dynamically from a content library.
    Can be used to create randomized assessments among other things.

    Note: technically, all matching blocks from the content library are added
    as children of this block, but only a subset of those children are shown to
    any particular student.
    """

    def _publish_event(self, event_name, result, **kwargs):
        """ Helper method to publish an event for analytics purposes """
        event_data = {
            "location": unicode(self.location),
            "result": result,
            "previous_count": getattr(self, "_last_event_result_count", len(self.selected)),
            "max_count": self.max_count,
        }
        event_data.update(kwargs)
        self.runtime.publish(self, "edx.librarycontentblock.content.{}".format(event_name), event_data)
        self._last_event_result_count = len(result)  # pylint: disable=attribute-defined-outside-init

    def selected_children(self):
        """
        Returns a set() of block_ids indicating which of the possible children
        have been selected to display to the current user.

        This reads and updates the "selected" field, which has user_state scope.

        Note: self.selected and the return value contain block_ids. To get
        actual BlockUsageLocators, it is necessary to use self.children,
        because the block_ids alone do not specify the block type.
        """
        if hasattr(self, "_selected_set"):
            # Already done:
            return self._selected_set  # pylint: disable=access-member-before-definition

        selected = set(tuple(k) for k in self.selected)  # set of (block_type, block_id) tuples assigned to this student

        lib_tools = self.runtime.service(self, 'library_tools')
        format_block_keys = lambda keys: lib_tools.create_block_analytics_summary(self.location.course_key, keys)

        # Determine which of our children we will show:
        valid_block_keys = set([(c.block_type, c.block_id) for c in self.children])  # pylint: disable=no-member
        # Remove any selected blocks that are no longer valid:
        invalid_block_keys = (selected - valid_block_keys)
        if invalid_block_keys:
            selected -= invalid_block_keys
            # Publish an event for analytics purposes:
            # reason "invalid" means deleted from library or a different library is now being used.
            self._publish_event(
                "removed",
                result=format_block_keys(selected),
                removed=format_block_keys(invalid_block_keys),
                reason="invalid"
            )
        # If max_count has been decreased, we may have to drop some previously selected blocks:
        overlimit_block_keys = set()
        while len(selected) > self.max_count:
            overlimit_block_keys.add(selected.pop())
        if overlimit_block_keys:
            # Publish an event for analytics purposes:
            self._publish_event(
                "removed",
                result=format_block_keys(selected),
                removed=format_block_keys(overlimit_block_keys),
                reason="overlimit"
            )
        # Do we have enough blocks now?
        num_to_add = self.max_count - len(selected)
        if num_to_add > 0:
            added_block_keys = None
            # We need to select [more] blocks to display to this user:
            pool = valid_block_keys - selected
            if self.mode == "random":
                num_to_add = min(len(pool), num_to_add)
                added_block_keys = set(random.sample(pool, num_to_add))
                # We now have the correct n random children to show for this user.
            else:
                raise NotImplementedError("Unsupported mode.")
            selected |= added_block_keys
            if added_block_keys:
                # Publish an event for analytics purposes:
                self._publish_event(
                    "assigned",
                    result=format_block_keys(selected),
                    added=format_block_keys(added_block_keys)
                )
        # Save our selections to the user state, to ensure consistency:
        self.selected = list(selected)  # TODO: this doesn't save from the LMS "Progress" page.
        # Cache the results
        self._selected_set = selected  # pylint: disable=attribute-defined-outside-init
        return selected

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
            for displayable in child.displayable_items():
                rendered_child = displayable.render(STUDENT_VIEW, child_context)
                fragment.add_frag_resources(rendered_child)
                contents.append({
                    'id': displayable.location.to_deprecated_string(),
                    'content': rendered_child.content,
                })

        fragment.add_content(self.system.render_template('vert_module.html', {
            'items': contents,
            'xblock_context': context,
        }))
        return fragment

    def validate(self):
        """
        Validates the state of this Library Content Module Instance.
        """
        return self.descriptor.validate()

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
                self.render_children(context, fragment, can_reorder=False, can_add=False)
        # else: When shown on a unit page, don't show any sort of preview -
        # just the status of this block in the validation area.

        # The following JS is used to make the "Update now" button work on the unit page and the container view:
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/library_content_edit.js'))
        fragment.initialize_js('LibraryContentAuthorView')
        return fragment

    def get_child_descriptors(self):
        """
        Return only the subset of our children relevant to the current student.
        """
        return list(self._get_selected_child_blocks())


@XBlock.wants('user')
@XBlock.wants('library_tools')  # Only needed in studio
@XBlock.wants('studio_user_permissions')  # Only available in studio
class LibraryContentDescriptor(LibraryContentFields, MakoModuleDescriptor, XmlDescriptor, StudioEditableDescriptor):
    """
    Descriptor class for LibraryContentModule XBlock.
    """
    module_class = LibraryContentModule
    mako_template = 'widgets/metadata-edit.html'
    js = {'coffee': [resource_string(__name__, 'js/src/vertical/edit.coffee')]}
    js_module_name = "VerticalDescriptor"

    @property
    def non_editable_metadata_fields(self):
        non_editable_fields = super(LibraryContentDescriptor, self).non_editable_metadata_fields
        # The only supported mode is currently 'random'.
        # Add the mode field to non_editable_metadata_fields so that it doesn't
        # render in the edit form.
        non_editable_fields.extend([LibraryContentFields.mode, LibraryContentFields.source_library_version])
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
    def refresh_children(self, request=None, suffix=None):  # pylint: disable=unused-argument
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
        user_id = self.get_user_id()
        if not self.tools:
            return Response("Library Tools unavailable in current runtime.", status=400)
        self.tools.update_children(self, user_id, user_perms)
        return Response()

    # Copy over any overridden settings the course author may have applied to the blocks.
    def _copy_overrides(self, store, user_id, source, dest):
        """
        Copy any overrides the user has made on blocks in this library.
        """
        for field in source.fields.itervalues():
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
        # pylint: disable=no-member
        if not self.tools:
            raise RuntimeError("Library tools unavailable, duplication will not be sane!")
        self.tools.update_children(self, user_id, user_perms, version=self.source_library_version)

        self._copy_overrides(store, user_id, source_block, self)

        # Children have been handled.
        return True

    def _validate_library_version(self, validation, lib_tools, version, library_key):
        """
        Validates library version
        """
        latest_version = lib_tools.get_library_version(library_key)
        if latest_version is not None:
            if version is None or version != unicode(latest_version):
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
        validation = super(LibraryContentDescriptor, self).validate()
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
        all_libraries = lib_tools.list_available_libraries()
        if user_perms:
            all_libraries = [
                (key, name) for key, name in all_libraries
                if user_perms.can_read(key) or self.source_library_id == unicode(key)
            ]
        all_libraries.sort(key=lambda entry: entry[1])  # Sort by name
        if self.source_library_id and self.source_library_key not in [entry[0] for entry in all_libraries]:
            all_libraries.append((self.source_library_id, _(u"Invalid Library")))
        all_libraries = [(u"", _("No Library Selected"))] + all_libraries
        values = [{"display_name": name, "value": unicode(key)} for key, name in all_libraries]
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
        for child in self._xmodule.get_child_descriptors():
            titles.extend(child.get_content_titles())
        return titles

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        children = [
            # pylint: disable=no-member
            system.process_xml(etree.tostring(child)).scope_ids.usage_id
            for child in xml_object.getchildren()
        ]
        definition = {
            attr_name: json.loads(attr_value)
            for attr_name, attr_value in xml_object.attrib
        }
        return definition, children

    def definition_to_xml(self, resource_fs):
        """ Exports Library Content Module to XML """
        # pylint: disable=no-member
        xml_object = etree.Element('library_content')
        for child in self.get_children():
            self.runtime.add_block_as_child_node(child, xml_object)
        # Set node attributes based on our fields.
        for field_name, field in self.fields.iteritems():
            if field_name in ('children', 'parent', 'content'):
                continue
            if field.is_set_on(self):
                xml_object.set(field_name, unicode(field.read_from(self)))
        return xml_object
