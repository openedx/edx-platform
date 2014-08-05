"""
Module for running content split tests
"""

import logging
import json
from webob import Response
from uuid import uuid4

from xmodule.progress import Progress
from xmodule.seq_module import SequenceDescriptor
from xmodule.studio_editable import StudioEditableModule, StudioEditableDescriptor
from xmodule.x_module import XModule, module_attr, STUDENT_VIEW
from xmodule.modulestore.inheritance import UserPartitionList

from lxml import etree

from xblock.core import XBlock
from xblock.fields import Scope, Integer, String, ReferenceValueDict
from xblock.fragment import Fragment

log = logging.getLogger('edx.' + __name__)

# Make '_' a no-op so we can scrape strings
_ = lambda text: text


class ValidationMessageType(object):
    """
    The type for a validation message -- currently 'information', 'warning' or 'error'.
    """
    information = 'information'
    warning = 'warning'
    error = 'error'

    @staticmethod
    def display_name(message_type):
        """
        Returns the display name for the specified validation message type.
        """
        if message_type == ValidationMessageType.warning:
            # Translators: This message will be added to the front of messages of type warning,
            # e.g. "Warning: this component has not been configured yet".
            return _(u"Warning")
        elif message_type == ValidationMessageType.error:
            # Translators: This message will be added to the front of messages of type error,
            # e.g. "Error: required field is missing".
            return _(u"Error")
        else:
            return None


# TODO: move this into the xblock repo once it has a formal validation contract
class ValidationMessage(object):
    """
    Represents a single validation message for an xblock.
    """
    def __init__(self, xblock, message_text, message_type, action_class=None, action_label=None):
        assert isinstance(message_text, unicode)
        self.xblock = xblock
        self.message_text = message_text
        self.message_type = message_type
        self.action_class = action_class
        self.action_label = action_label

    def __unicode__(self):
        return self.message_text


class SplitTestFields(object):
    """Fields needed for split test module"""
    has_children = True

    # All available user partitions (with value and display name). This is updated each time
    # editable_metadata_fields is called.
    user_partition_values = []
    # Default value used for user_partition_id
    no_partition_selected = {'display_name': _("Not Selected"), 'value': -1}

    @staticmethod
    def build_partition_values(all_user_partitions, selected_user_partition):
        """
        This helper method builds up the user_partition values that will
        be passed to the Studio editor
        """
        SplitTestFields.user_partition_values = []
        # Add "No selection" value if there is not a valid selected user partition.
        if not selected_user_partition:
            SplitTestFields.user_partition_values.append(SplitTestFields.no_partition_selected)
        for user_partition in all_user_partitions:
            SplitTestFields.user_partition_values.append({"display_name": user_partition.name, "value": user_partition.id})
        return SplitTestFields.user_partition_values

    display_name = String(
        display_name=_("Display Name"),
        help=_("This name is used for organizing your course content, but is not shown to students."),
        scope=Scope.settings,
        default=_("Content Experiment")
    )

    # Specified here so we can see what the value set at the course-level is.
    user_partitions = UserPartitionList(
        help=_("The list of group configurations for partitioning students in content experiments."),
        default=[],
        scope=Scope.settings
    )

    user_partition_id = Integer(
        help=_("The configuration defines how users are grouped for this content experiment. Caution: Changing the group configuration of a student-visible experiment will impact the experiment data."),
        scope=Scope.content,
        display_name=_("Group Configuration"),
        default=no_partition_selected["value"],
        values=lambda: SplitTestFields.user_partition_values  # Will be populated before the Studio editor is shown.
    )

    # group_id is an int
    # child is a serialized UsageId (aka Location).  This child
    # location needs to actually match one of the children of this
    # Block.  (expected invariant that we'll need to test, and handle
    # authoring tools that mess this up)

    # TODO: is there a way to add some validation around this, to
    # be run on course load or in studio or ....

    group_id_to_child = ReferenceValueDict(
        help=_("Which child module students in a particular group_id should see"),
        scope=Scope.content
    )


@XBlock.needs('user_tags')  # pylint: disable=abstract-method
@XBlock.wants('partitions')
class SplitTestModule(SplitTestFields, XModule, StudioEditableModule):
    """
    Show the user the appropriate child.  Uses the ExperimentState
    API to figure out which child to show.

    Course staff still get put in an experimental condition, but have the option
    to see the other conditions.  The only thing that counts toward their
    grade/progress is the condition they are actually in.

    Technical notes:
      - There is more dark magic in this code than I'd like.  The whole varying-children +
        grading interaction is a tangle between super and subclasses of descriptors and
        modules.
    """

    def __init__(self, *args, **kwargs):

        super(SplitTestModule, self).__init__(*args, **kwargs)

        self.child_descriptor = None
        child_descriptors = self.get_child_descriptors()
        if len(child_descriptors) >= 1:
            self.child_descriptor = child_descriptors[0]
        if self.child_descriptor is not None:
            self.child = self.system.get_module(self.child_descriptor)
        else:
            self.child = None

    def get_child_descriptor_by_location(self, location):
        """
        Look through the children and look for one with the given location.
        Returns the descriptor.
        If none match, return None
        """
        # NOTE: calling self.get_children() creates a circular reference--
        # it calls get_child_descriptors() internally, but that doesn't work until
        # we've picked a choice.  Use self.descriptor.get_children() instead.

        for child in self.descriptor.get_children():
            if child.location == location:
                return child

        return None

    def get_content_titles(self):
        """
        Returns list of content titles for split_test's child.

        This overwrites the get_content_titles method included in x_module by default.

        WHY THIS OVERWRITE IS NECESSARY: If we fetch *all* of split_test's children,
        we'll end up getting all of the possible conditions users could ever see.
        Ex: If split_test shows a video to group A and HTML to group B, the
        regular get_content_titles in x_module will get the title of BOTH the video
        AND the HTML.

        We only want the content titles that should actually be displayed to the user.

        split_test's .child property contains *only* the child that should actually
        be shown to the user, so we call get_content_titles() on only that child.
        """
        return self.child.get_content_titles()

    def get_child_descriptors(self):
        """
        For grading--return just the chosen child.
        """
        group_id = self.get_group_id()
        if group_id is None:
            return []

        # group_id_to_child comes from json, so it has to have string keys
        str_group_id = str(group_id)
        if str_group_id in self.group_id_to_child:
            child_location = self.group_id_to_child[str_group_id]
            child_descriptor = self.get_child_descriptor_by_location(child_location)
        else:
            # Oops.  Config error.
            log.debug("configuration error in split test module: invalid group_id %r (not one of %r).  Showing error", str_group_id, self.group_id_to_child.keys())

        if child_descriptor is None:
            # Peak confusion is great.  Now that we set child_descriptor,
            # get_children() should return a list with one element--the
            # xmodule for the child
            log.debug("configuration error in split test module: no such child")
            return []

        return [child_descriptor]

    def get_group_id(self):
        """
        Returns the group ID, or None if none is available.
        """
        partitions_service = self.runtime.service(self, 'partitions')
        if not partitions_service:
            return None
        return partitions_service.get_user_group_for_partition(self.user_partition_id)

    def _staff_view(self, context):
        """
        Render the staff view for a split test module.
        """
        fragment = Fragment()
        contents = []

        for group_id in self.group_id_to_child:
            child_location = self.group_id_to_child[group_id]
            child_descriptor = self.get_child_descriptor_by_location(child_location)
            child = self.system.get_module(child_descriptor)
            rendered_child = child.render(STUDENT_VIEW, context)
            fragment.add_frag_resources(rendered_child)

            contents.append({
                'group_id': group_id,
                'id': child.location.to_deprecated_string(),
                'content': rendered_child.content
            })

        # Use the new template
        fragment.add_content(self.system.render_template('split_test_staff_view.html', {
            'items': contents,
        }))
        fragment.add_css('.split-test-child { display: none; }')
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/split_test_staff.js'))
        fragment.initialize_js('ABTestSelector')
        return fragment

    def author_view(self, context):
        """
        Renders the Studio preview by rendering each child so that they can all be seen and edited.
        """
        fragment = Fragment()
        root_xblock = context.get('root_xblock')
        is_configured = not self.user_partition_id == SplitTestFields.no_partition_selected['value']
        is_root = root_xblock and root_xblock.location == self.location
        active_groups_preview = None
        inactive_groups_preview = None

        if is_root:
            [active_children, inactive_children] = self.descriptor.active_and_inactive_children()
            active_groups_preview = self.studio_render_children(
                fragment, active_children, context
            )
            inactive_groups_preview = self.studio_render_children(
                fragment, inactive_children, context
            )

        fragment.add_content(self.system.render_template('split_test_author_view.html', {
            'split_test': self,
            'is_root': is_root,
            'is_configured': is_configured,
            'active_groups_preview': active_groups_preview,
            'inactive_groups_preview': inactive_groups_preview,
            'group_configuration_url': self.descriptor.group_configuration_url,
        }))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/split_test_author_view.js'))
        fragment.initialize_js('SplitTestAuthorView')

        return fragment

    def studio_render_children(self, fragment, children, context):
        """
        Renders the specified children and returns it as an HTML string. In addition, any
        dependencies are added to the specified fragment.
        """
        html = ""
        for active_child_descriptor in children:
            active_child = self.system.get_module(active_child_descriptor)
            rendered_child = active_child.render(StudioEditableModule.get_preview_view_name(active_child), context)
            fragment.add_frag_resources(rendered_child)
            html = html + rendered_child.content
        return html

    def student_view(self, context):
        """
        Renders the contents of the chosen condition for students, and all the
        conditions for staff.
        """
        if self.child is None:
            # raise error instead?  In fact, could complain on descriptor load...
            return Fragment(content=u"<div>Nothing here.  Move along.</div>")

        if self.system.user_is_staff:
            return self._staff_view(context)
        else:
            child_fragment = self.child.render(STUDENT_VIEW, context)
            fragment = Fragment(self.system.render_template('split_test_student_view.html', {
                'child_content': child_fragment.content,
                'child_id': self.child.scope_ids.usage_id,
            }))
            fragment.add_frag_resources(child_fragment)
            fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/split_test_student.js'))
            fragment.initialize_js('SplitTestStudentView')
            return fragment

    @XBlock.handler
    def log_child_render(self, request, suffix=''):  # pylint: disable=unused-argument
        """
        Record in the tracking logs which child was rendered
        """
        # TODO: use publish instead, when publish is wired to the tracking logs
        self.system.track_function('xblock.split_test.child_render', {'child-id': self.child.scope_ids.usage_id.to_deprecated_string()})
        return Response()

    def get_icon_class(self):
        return self.child.get_icon_class() if self.child else 'other'

    def get_progress(self):
        children = self.get_children()
        progresses = [child.get_progress() for child in children]
        progress = reduce(Progress.add_counts, progresses, None)
        return progress


@XBlock.needs('user_tags')  # pylint: disable=abstract-method
@XBlock.wants('partitions')
@XBlock.wants('user')
class SplitTestDescriptor(SplitTestFields, SequenceDescriptor, StudioEditableDescriptor):
    # the editing interface can be the same as for sequences -- just a container
    module_class = SplitTestModule

    filename_extension = "xml"

    mako_template = "widgets/metadata-only-edit.html"

    child_descriptor = module_attr('child_descriptor')
    log_child_render = module_attr('log_child_render')
    get_content_titles = module_attr('get_content_titles')

    def definition_to_xml(self, resource_fs):
        xml_object = etree.Element('split_test')
        renderable_groups = {}
        # json.dumps doesn't know how to handle Location objects
        for group in self.group_id_to_child:
            renderable_groups[group] = self.group_id_to_child[group].to_deprecated_string()
        xml_object.set('group_id_to_child', json.dumps(renderable_groups))
        xml_object.set('user_partition_id', str(self.user_partition_id))
        for child in self.get_children():
            self.runtime.add_block_as_child_node(child, xml_object)
        return xml_object

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        children = []
        raw_group_id_to_child = xml_object.attrib.get('group_id_to_child', None)
        user_partition_id = xml_object.attrib.get('user_partition_id', None)
        try:
            group_id_to_child = json.loads(raw_group_id_to_child)
        except ValueError:
            msg = "group_id_to_child is not valid json"
            log.exception(msg)
            system.error_tracker(msg)

        for child in xml_object:
            try:
                descriptor = system.process_xml(etree.tostring(child))
                children.append(descriptor.scope_ids.usage_id)
            except Exception:
                msg = "Unable to load child when parsing split_test module."
                log.exception(msg)
                system.error_tracker(msg)

        return ({
            'group_id_to_child': group_id_to_child,
            'user_partition_id': user_partition_id
        }, children)

    def get_context(self):
        _context = super(SplitTestDescriptor, self).get_context()
        _context.update({
            'selected_partition': self.get_selected_partition()
        })
        return _context

    def has_dynamic_children(self):
        """
        Grading needs to know that only one of the children is actually "real".  This
        makes it use module.get_child_descriptors().
        """
        return True

    def editor_saved(self, user, old_metadata, old_content):
        """
        Used to create default verticals for the groups.

        Assumes that a mutable modulestore is being used.
        """
        # Any existing value of user_partition_id will be in "old_content" instead of "old_metadata"
        # because it is Scope.content.
        if 'user_partition_id' not in old_content or old_content['user_partition_id'] != self.user_partition_id:
            selected_partition = self.get_selected_partition()
            if selected_partition is not None:
                self.group_id_mapping = {}  # pylint: disable=attribute-defined-outside-init
                for group in selected_partition.groups:
                    self._create_vertical_for_group(group, user.id)
                # Don't need to call update_item in the modulestore because the caller of this method will do it.
        else:
            # If children referenced in group_id_to_child have been deleted, remove them from the map.
            for str_group_id, usage_key in self.group_id_to_child.items():
                if usage_key not in self.children:  # pylint: disable=no-member
                    del self.group_id_to_child[str_group_id]

    @property
    def editable_metadata_fields(self):
        # Update the list of partitions based on the currently available user_partitions.
        SplitTestFields.build_partition_values(self.user_partitions, self.get_selected_partition())

        editable_fields = super(SplitTestDescriptor, self).editable_metadata_fields

        # Explicitly add user_partition_id, which does not automatically get picked up because it is Scope.content.
        # Note that this means it will be saved by the Studio editor as "metadata", but the field will
        # still update correctly.
        editable_fields[SplitTestFields.user_partition_id.name] = self._create_metadata_editor_info(
            SplitTestFields.user_partition_id
        )

        return editable_fields

    @property
    def non_editable_metadata_fields(self):
        non_editable_fields = super(SplitTestDescriptor, self).non_editable_metadata_fields
        non_editable_fields.extend([
            SplitTestDescriptor.due,
            SplitTestDescriptor.user_partitions
        ])
        return non_editable_fields

    def get_selected_partition(self):
        """
        Returns the partition that this split module is currently using, or None
        if the currently selected partition ID does not match any of the defined partitions.
        """
        for user_partition in self.user_partitions:
            if user_partition.id == self.user_partition_id:
                return user_partition

        return None

    def active_and_inactive_children(self):
        """
        Returns two values:
        1. The active children of this split test, in the order of the groups.
        2. The remaining (inactive) children, in the order they were added to the split test.
        """
        children = self.get_children()

        user_partition = self.get_selected_partition()
        if not user_partition:
            return [], children

        def get_child_descriptor(location):
            """
            Returns the child descriptor which matches the specified location, or None if one is not found.
            """
            for child in children:
                if child.location == location:
                    return child
            return None

        # Compute the active children in the order specified by the user partition
        active_children = []
        for group in user_partition.groups:
            group_id = unicode(group.id)
            child_location = self.group_id_to_child.get(group_id, None)
            child = get_child_descriptor(child_location)
            if child:
                active_children.append(child)

        # Compute the inactive children in the order they were added to the split test
        inactive_children = [child for child in children if child not in active_children]

        return active_children, inactive_children

    def validation_messages(self):
        """
        Returns a list of validation messages describing the current state of the block. Each message
        includes a message type indicating whether the message represents information, a warning or an error.
        """
        _ = self.runtime.service(self, "i18n").ugettext  # pylint: disable=redefined-outer-name
        messages = []
        if self.user_partition_id < 0:
            messages.append(ValidationMessage(
                self,
                _(u"The experiment is not associated with a group configuration."),
                ValidationMessageType.warning,
                'edit-button',
                _(u"Select a Group Configuration")
            ))
        else:
            user_partition = self.get_selected_partition()
            if not user_partition:
                messages.append(ValidationMessage(
                    self,
                    _(u"The experiment uses a deleted group configuration. Select a valid group configuration or delete this experiment."),
                    ValidationMessageType.error
                ))
            else:
                [active_children, inactive_children] = self.active_and_inactive_children()
                if len(active_children) < len(user_partition.groups):
                    messages.append(ValidationMessage(
                        self,
                        _(u"The experiment does not contain all of the groups in the configuration."),
                        ValidationMessageType.error,
                        'add-missing-groups-button',
                        _(u"Add Missing Groups")
                    ))
                if len(inactive_children) > 0:
                    messages.append(ValidationMessage(
                        self,
                        _(u"The experiment has an inactive group. Move content into active groups, then delete the inactive group."),
                        ValidationMessageType.warning
                    ))
        return messages

    @XBlock.handler
    def add_missing_groups(self, request, suffix=''):  # pylint: disable=unused-argument
        """
        Create verticals for any missing groups in the split test instance.

        Called from Studio view.
        """
        user_partition = self.get_selected_partition()

        changed = False
        for group in user_partition.groups:
            str_group_id = unicode(group.id)
            if str_group_id not in self.group_id_to_child:
                user_id = self.runtime.service(self, 'user').user_id
                self._create_vertical_for_group(group, user_id)
                changed = True

        if changed:
            # TODO user.id - to be fixed by Publishing team
            self.system.modulestore.update_item(self, None)
        return Response()

    @property
    def group_configuration_url(self):
        assert hasattr(self.system, 'modulestore') and hasattr(self.system.modulestore, 'get_course'), \
            "modulestore has to be available"

        course_module = self.system.modulestore.get_course(self.location.course_key)
        group_configuration_url = None
        if 'split_test' in course_module.advanced_modules:
            user_partition = self.get_selected_partition()
            if user_partition:
                group_configuration_url = "{url}#{configuration_id}".format(
                    url='/group_configurations/' + unicode(self.location.course_key),
                    configuration_id=str(user_partition.id)
                )

        return group_configuration_url

    def _create_vertical_for_group(self, group, user_id):
        """
        Creates a vertical to associate with the group.

        This appends the new vertical to the end of children, and updates group_id_to_child.
        A mutable modulestore is needed to call this method (will need to update after mixed
        modulestore work, currently relies on mongo's create_item method).
        """
        assert hasattr(self.system, 'modulestore') and hasattr(self.system.modulestore, 'create_item'), \
            "editor_saved should only be called when a mutable modulestore is available"
        modulestore = self.system.modulestore
        dest_usage_key = self.location.replace(category="vertical", name=uuid4().hex)
        metadata = {'display_name': group.name}
        modulestore.create_item(
            user_id,
            self.location.course_key,
            dest_usage_key.block_type,
            block_id=dest_usage_key.block_id,
            definition_data=None,
            metadata=metadata,
            runtime=self.system,
        )
        self.children.append(dest_usage_key)  # pylint: disable=no-member
        self.group_id_to_child[unicode(group.id)] = dest_usage_key

    @property
    def general_validation_message(self):
        """
        Message for either error or warning validation message/s.

        Returns message and type. Priority given to error type message.
        """
        validation_messages = self.validation_messages()
        if validation_messages:
            has_error = any(message.message_type == ValidationMessageType.error for message in validation_messages)
            return {
                'message': _(u"This content experiment has issues that affect content visibility."),
                'type': ValidationMessageType.error if has_error else ValidationMessageType.warning,
            }
        return None
