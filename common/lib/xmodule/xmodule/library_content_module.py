# -*- coding: utf-8 -*-
"""
LibraryContent: The XBlock used to include blocks from a library in a course.
"""
from bson.objectid import ObjectId, InvalidId
from collections import namedtuple
from copy import copy
from capa.responsetypes import registry
from gettext import ngettext

from .mako_module import MakoModuleDescriptor
from opaque_keys import InvalidKeyError
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


def enum(**enums):
    """ enum helper in lieu of enum34 """
    return type('Enum', (), enums)


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


class LibraryVersionReference(namedtuple("LibraryVersionReference", "library_id version")):
    """
    A reference to a specific library, with an optional version.
    The version is used to find out when the LibraryContentXBlock was last
    updated with the latest content from the library.

    library_id is a LibraryLocator
    version is an ObjectId or None
    """
    def __new__(cls, library_id, version=None):
        # pylint: disable=super-on-old-class
        if not isinstance(library_id, LibraryLocator):
            library_id = LibraryLocator.from_string(library_id)
        if library_id.version_guid:
            assert (version is None) or (version == library_id.version_guid)
            if not version:
                version = library_id.version_guid
            library_id = library_id.for_version(None)
        if version and not isinstance(version, ObjectId):
            try:
                version = ObjectId(version)
            except InvalidId:
                raise ValueError(version)
        return super(LibraryVersionReference, cls).__new__(cls, library_id, version)

    @staticmethod
    def from_json(value):
        """
        Implement from_json to convert from JSON
        """
        return LibraryVersionReference(*value)

    def to_json(self):
        """
        Implement to_json to convert value to JSON
        """
        # TODO: Is there anyway for an xblock to *store* an ObjectId as
        # part of the List() field value?
        return [unicode(self.library_id), unicode(self.version) if self.version else None]  # pylint: disable=no-member


class LibraryList(List):
    """
    Special List class for listing references to content libraries.
    Is simply a list of LibraryVersionReference tuples.
    """
    def from_json(self, values):
        """
        Implement from_json to convert from JSON.

        values might be a list of lists, or a list of strings
        Normally the runtime gives us:
            [[u'library-v1:ProblemX+PR0B', '5436ffec56c02c13806a4c1b'], ...]
        But the studio editor gives us:
            [u'library-v1:ProblemX+PR0B,5436ffec56c02c13806a4c1b', ...]
        """
        def parse(val):
            """ Convert this list entry from its JSON representation """
            if isinstance(val, basestring):
                val = val.strip(' []')
                parts = val.rsplit(',', 1)
                val = [parts[0], parts[1] if len(parts) > 1 else None]
            try:
                return LibraryVersionReference.from_json(val)
            except InvalidKeyError:
                try:
                    friendly_val = val[0]  # Just get the library key part, not the version
                except IndexError:
                    friendly_val = unicode(val)
                raise ValueError(_('"{value}" is not a valid library ID.').format(value=friendly_val))
        return [parse(v) for v in values]

    def to_json(self, values):
        """
        Implement to_json to convert value to JSON
        """
        return [lvr.to_json() for lvr in values]


class LibraryContentFields(object):
    """
    Fields for the LibraryContentModule.

    Separated out for now because they need to be added to the module and the
    descriptor.
    """
    # Please note the display_name of each field below is used in
    # common/test/acceptance/pages/studio/overview.py:StudioLibraryContentXBlockEditModal
    # to locate input elements - keep synchronized
    display_name = String(
        display_name=_("Display Name"),
        help=_("Display name for this module"),
        default="Randomized Content Block",
        scope=Scope.settings,
    )
    source_libraries = LibraryList(
        display_name=_("Libraries"),
        help=_("Enter a library ID for each library from which you want to draw content."),
        default=[],
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
        previous_count = len(selected)

        lib_tools = self.runtime.service(self, 'library_tools')
        format_block_keys = lambda keys: lib_tools.create_block_analytics_summary(self.location.course_key, keys)

        def publish_event(event_name, **kwargs):
            """ Publish an event for analytics purposes """
            event_data = {
                "location": unicode(self.location),
                "result": format_block_keys(selected),
                "previous_count": previous_count,
                "max_count": self.max_count,
            }
            event_data.update(kwargs)
            self.runtime.publish(self, "edx.librarycontentblock.content.{}".format(event_name), event_data)

        # Determine which of our children we will show:
        valid_block_keys = set([(c.block_type, c.block_id) for c in self.children])  # pylint: disable=no-member
        # Remove any selected blocks that are no longer valid:
        invalid_block_keys = (selected - valid_block_keys)
        if invalid_block_keys:
            selected -= invalid_block_keys
            # Publish an event for analytics purposes:
            # reason "invalid" means deleted from library or a different library is now being used.
            publish_event("removed", removed=format_block_keys(invalid_block_keys), reason="invalid")
        # If max_count has been decreased, we may have to drop some previously selected blocks:
        overlimit_block_keys = set()
        while len(selected) > self.max_count:
            overlimit_block_keys.add(selected.pop())
        if overlimit_block_keys:
            # Publish an event for analytics purposes:
            publish_event("removed", removed=format_block_keys(overlimit_block_keys), reason="overlimit")
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
                publish_event("assigned", added=format_block_keys(added_block_keys))
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
        non_editable_fields.append(LibraryContentFields.mode)
        return non_editable_fields

    @XBlock.handler
    def refresh_children(self, request=None, suffix=None):  # pylint: disable=unused-argument
        """
        Refresh children:
        This method is to be used when any of the libraries that this block
        references have been updated. It will re-fetch all matching blocks from
        the libraries, and copy them as children of this block. The children
        will be given new block_ids, but the definition ID used should be the
        exact same definition ID used in the library.

        This method will update this block's 'source_libraries' field to store
        the version number of the libraries used, so we easily determine if
        this block is up to date or not.
        """
        lib_tools = self.runtime.service(self, 'library_tools')
        user_service = self.runtime.service(self, 'user')
        user_perms = self.runtime.service(self, 'studio_user_permissions')
        if user_service:
            # May be None when creating bok choy test fixtures
            user_id = user_service.get_current_user().opt_attrs.get('edx-platform.user_id', None)
        else:
            user_id = None
        lib_tools.update_children(self, user_id, user_perms)
        return Response()

    def _validate_library_version(self, validation, lib_tools, version, library_key):
        """
        Validates library version
        """
        latest_version = lib_tools.get_library_version(library_key)
        if latest_version is not None:
            if version is None or version != latest_version:
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
        if not self.source_libraries:
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
        for library_key, version in self.source_libraries:
            if not self._validate_library_version(validation, lib_tools, version, library_key):
                break

        # Note: we assume refresh_children() has been called
        # since the last time fields like source_libraries or capa_types were changed.
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
                            u'The specified libraries are configured to fetch {count} problem, ',
                            u'The specified libraries are configured to fetch {count} problems, ',
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

    def editor_saved(self, user, old_metadata, old_content):
        """
        If source_libraries or capa_type has been edited, refresh_children automatically.
        """
        old_source_libraries = LibraryList().from_json(old_metadata.get('source_libraries', []))
        if (set(old_source_libraries) != set(self.source_libraries) or
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
        """ XML support not yet implemented. """
        raise NotImplementedError

    def definition_to_xml(self, resource_fs):
        """ XML support not yet implemented. """
        raise NotImplementedError

    @classmethod
    def from_xml(cls, xml_data, system, id_generator):
        """ XML support not yet implemented. """
        raise NotImplementedError

    def export_to_xml(self, resource_fs):
        """ XML support not yet implemented. """
        raise NotImplementedError
