"""
Module for running content split tests
"""

import logging
import json
from webob import Response

from xmodule.progress import Progress
from xmodule.seq_module import SequenceDescriptor
from xmodule.studio_editable import StudioEditableModule
from xmodule.x_module import XModule, module_attr

from lxml import etree

from xblock.core import XBlock
from xblock.fields import Scope, Integer, String, ReferenceValueDict
from xblock.fragment import Fragment

log = logging.getLogger('edx.' + __name__)


class SplitTestFields(object):
    """Fields needed for split test module"""
    has_children = True

    display_name = String(
        display_name="Display Name",
        help="This name appears in the horizontal navigation at the top of the page.",
        scope=Scope.settings,
        default="Experiment Block"
    )

    user_partition_id = Integer(
        help="Which user partition is used for this test",
        scope=Scope.content
    )

    # group_id is an int
    # child is a serialized UsageId (aka Location).  This child
    # location needs to actually match one of the children of this
    # Block.  (expected invariant that we'll need to test, and handle
    # authoring tools that mess this up)

    # TODO: is there a way to add some validation around this, to
    # be run on course load or in studio or ....

    group_id_to_child = ReferenceValueDict(
        help="Which child module students in a particular group_id should see",
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
            rendered_child = child.render('student_view', context)
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

    def studio_preview_view(self, context):
        """
        Renders the Studio preview by rendering each child so that they can all be seen and edited.
        """
        fragment = Fragment()
        # Only render the children when this block is being shown as the container
        root_xblock = context.get('root_xblock')
        if root_xblock and root_xblock.location == self.location:
            self.render_children(context, fragment, can_reorder=False)
        return fragment

    def student_view(self, context):
        """
        Render the contents of the chosen condition for students, and all the
        conditions for staff.
        """
        # When rendering a Studio preview, render all of the block's children
        if context and context.get('runtime_type', None) == 'studio':
            return self.studio_preview_view(context)

        if self.child is None:
            # raise error instead?  In fact, could complain on descriptor load...
            return Fragment(content=u"<div>Nothing here.  Move along.</div>")

        if self.system.user_is_staff:
            return self._staff_view(context)
        else:
            child_fragment = self.child.render('student_view', context)
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
        self.system.track_function('xblock.split_test.child_render', {'child-id': self.child.scope_ids.usage_id})
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
class SplitTestDescriptor(SplitTestFields, SequenceDescriptor):
    # the editing interface can be the same as for sequences -- just a container
    module_class = SplitTestModule

    filename_extension = "xml"

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

    def has_dynamic_children(self):
        """
        Grading needs to know that only one of the children is actually "real".  This
        makes it use module.get_child_descriptors().
        """
        return True

    @property
    def non_editable_metadata_fields(self):
        non_editable_fields = super(SplitTestDescriptor, self).non_editable_metadata_fields
        non_editable_fields.extend([
            SplitTestDescriptor.due,
        ])
        return non_editable_fields
