"""
Module for running content split tests
"""

import logging
from webob import Response

from xmodule.progress import Progress
from xmodule.seq_module import SequenceDescriptor
from xmodule.x_module import XModule, module_attr

from lxml import etree

from xblock.core import XBlock
from xblock.fields import Scope, Integer, Dict
from xblock.fragment import Fragment

log = logging.getLogger('edx.' + __name__)


class SplitTestFields(object):
    """Fields needed for split test module"""
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


@XBlock.needs('user_tags')
@XBlock.needs('partitions')
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

        super(SplitTestModule, self).__init__(*args, **kwargs)

        self.child_descriptor = self.get_child_descriptors()[0]
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
            if child.location.url() == location:
                return child

        return None

    def get_child_descriptors(self):
        """
        For grading--return just the chosen child.
        """
        group_id = self.runtime.service(self, 'partitions').get_user_group_for_partition(self.user_partition_id)

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
                'id': child.id,
                'content': rendered_child.content
            })

        # Use the new template
        fragment.add_content(self.system.render_template('split_test_staff_view.html', {
            'items': contents,
        }))
        fragment.add_css('.split-test-child { display: none; }');
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/split_test_staff.js'))
        fragment.initialize_js('ABTestSelector')
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
    def log_child_render(self, _request, _suffix=''):
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


@XBlock.needs('user_tags')
@XBlock.needs('partitions')
class SplitTestDescriptor(SplitTestFields, SequenceDescriptor):
    # the editing interface can be the same as for sequences -- just a container
    module_class = SplitTestModule

    filename_extension = "xml"

    child_descriptor = module_attr('child_descriptor')
    log_child_render = module_attr('log_child_render')

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
