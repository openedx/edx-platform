import logging
import random

from xmodule.partitions.partitions import UserPartition, Group
from xmodule.partitions.partitions_service import get_user_group_for_partition
from xmodule.progress import Progress
from xmodule.seq_module import SequenceDescriptor
from xmodule.x_module import XModule

from lxml import etree

from xblock.fields import Scope, Integer, Dict, List
from xblock.fragment import Fragment

log = logging.getLogger('edx.' + __name__)


class SplitTestFields(object):
    user_partition_id = Integer(help="Which user partition is used for this test",
                                   scope=Scope.content)

    # group_id is an int
    # child is a serialized UsageId (aka Location).  This child
    # location needs to actually match one of the children of this
    # Block.  (expected invariant that we'll need to test, and handle
    # authoring tools that mess this up)

    # TODO: is there a way to add some validation around this, to
    # be run on course load or in studio or ....

    group_id_to_child = Dict(help="Which child module students in a particular "
                             "group_id should see",
                             scope=Scope.content)



class SplitTestModule(SplitTestFields, XModule):
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
        super(SplitTestFields, self).__init__(*args, **kwargs)

        group_id = get_user_group_for_partition(self.runtime, self.user_partition_id)

        # group_id_to_child comes from json, so it has to have string keys
        str_group_id = str(group_id)
        if str_group_id in self.group_id_to_child:
            child_location = self.group_id_to_child[str_group_id]
            self.child_descriptor = self.get_child_descriptor_by_location(child_location)
        else:
            # Oops.  Config error.
            # TODO: better error message
            log.debug("split test config error: invalid group_id.  Showing error")
            self.child_descriptor = None

        if self.child_descriptor is not None:
            # Peak confusion is great.  Now that we set child_descriptor,
            # get_children() should return a list with one element--the
            # xmodule for the child
            self.child = self.get_children()[0]
        else:
            # TODO: better error message
            log.debug("split test config error: no such child")
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
            if child.location.url() == location:
                return child

        return None


    def get_child_descriptors(self):
        """
        For grading--return just the chosen child.
        """
        if self.child_descriptor is None:
            return []

        return [self.child_descriptor]


    def _actually_get_all_children(self):
        """
        Actually get all the child blocks of this block, instead of
        get_children(), which will only get the ones we want to expose to
        progress/grading/etc for this user.  Used to show staff all the options
        of a split test, even while they are technically only in one of the
        buckets.

        (Aside: this feels like too much magic)
        """
        # Note: this deliberately uses system.get_module() because we're using
        # XModule children for now (also see comment in
        # x_module.py:get_children())
        return [self.system.get_module(descriptor)
                for descriptor in self.descriptor.get_children()]


    def _get_experiment_definition():
        """
        TODO: what interface should this actually use?
        """

    def _staff_view(self, context):
        """
        Render the staff view for a split test module.
        """
        # TODO (architectural): To give children proper context (e.g. which
        # conditions are which), this block will need access to the actual
        # UserPartition definition, not just the user's condition.
        #
        # This seems to require either:
        # a way to get to the Course object, or exposing the UserPartitionList
        # in the runtime.
        fragment = Fragment()
        contents = []

        for child in self._actually_get_all_children():
            rendered_child = child.render('student_view', context)
            fragment.add_frag_resources(rendered_child)

            contents.append({
                'id': child.id,
                'content': rendered_child.content
                })

        # Use the existing vertical template for now.
        # TODO: replace this with a dropdown, defaulting to user's condition
        fragment.add_content(self.system.render_template('vert_module.html', {
            'items': contents
            }))
        return fragment


    def student_view(self, context):
        """
        Render the contents of the chosen condition for students, and all the
        conditions for staff.
        """
        if self.child is None:
            # raise error instead?  In fact, could complain on descriptor load...
            return Fragment(content=u"<div>Nothing here.  Move along.</div>")

        if self.system.user_is_staff:
            return self._staff_view(context)
        else:
            return self.child.render('student_view', context)


    def get_icon_class(self):
        return self.child.get_icon_class() if self.child else 'other'


    def get_progress(self):
        children = self.get_children()
        progresses = [child.get_progress() for child in children]
        progress = reduce(Progress.add_counts, progresses, None)
        return progress



class SplitTestDescriptor(SplitTestFields, SequenceDescriptor):
    # the editing interface can be the same as for sequences -- just a container
    module_class = SplitTestModule

    filename_extension = "xml"

    def definition_to_xml(self, resource_fs):

        xml_object = etree.Element('split_test')
        # TODO: also save the experiment id and the condition map
        for child in self.get_children():
            xml_object.append(
                etree.fromstring(child.export_to_xml(resource_fs)))
        return xml_object


    def has_dynamic_children(self):
        """
        Grading needs to know that only one of the children is actually "real".  This
        makes it use module.get_child_descriptors().
        """
        return True
