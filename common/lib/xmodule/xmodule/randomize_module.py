

import logging
import random

from lxml import etree
from web_fragments.fragment import Fragment
from xblock.fields import Integer, Scope
from xmodule.seq_module import SequenceDescriptor
from xmodule.x_module import STUDENT_VIEW, XModule

log = logging.getLogger('edx.' + __name__)


class RandomizeFields(object):
    choice = Integer(help="Which random child was chosen", scope=Scope.user_state)


class RandomizeModule(RandomizeFields, XModule):
    """
    Chooses a random child module.  Chooses the same one every time for each student.

     Example:
     <randomize>
     <problem url_name="problem1" />
     <problem url_name="problem2" />
     <problem url_name="problem3" />
     </randomize>

    User notes:

      - If you're randomizing amongst graded modules, each of them MUST be worth the same
        number of points.  Otherwise, the earth will be overrun by monsters from the
        deeps.  You have been warned.

    Technical notes:
      - There is more dark magic in this code than I'd like.  The whole varying-children +
        grading interaction is a tangle between super and subclasses of descriptors and
        modules.
"""
    def __init__(self, *args, **kwargs):
        super(RandomizeModule, self).__init__(*args, **kwargs)

        # NOTE: calling self.get_children() doesn't work until we've picked a choice
        num_choices = len(self.descriptor.get_children())

        if self.choice is not None and self.choice > num_choices:
            # Oops.  Children changed. Reset.
            self.choice = None

        if self.choice is None:
            # choose one based on the system seed, or randomly if that's not available
            if num_choices > 0:
                if self.system.seed is not None:
                    self.choice = self.system.seed % num_choices
                else:
                    self.choice = random.randrange(0, num_choices)

        if self.choice is not None:
            # Now get_children() should return a list with one element
            log.debug("children of randomize module (should be only 1): %s", self.child)

    @property
    def child_descriptor(self):
        """ Return descriptor of selected choice """
        if self.choice is None:
            return None
        return self.descriptor.get_children()[self.choice]

    @property
    def child(self):
        """ Return module instance of selected choice """
        child_descriptor = self.child_descriptor
        if child_descriptor is None:
            return None
        return self.system.get_module(child_descriptor)

    def get_child_descriptors(self):
        """
        For grading--return just the chosen child.
        """
        if self.child_descriptor is None:
            return []

        return [self.child_descriptor]

    def student_view(self, context):
        if self.child is None:
            # raise error instead?  In fact, could complain on descriptor load...
            return Fragment(content=u"<div>Nothing to randomize between</div>")

        return self.child.render(STUDENT_VIEW, context)

    def get_icon_class(self):
        return self.child.get_icon_class() if self.child else 'other'


class RandomizeDescriptor(RandomizeFields, SequenceDescriptor):
    # the editing interface can be the same as for sequences -- just a container
    module_class = RandomizeModule
    resources_dir = None

    filename_extension = "xml"

    show_in_read_only_mode = True

    def definition_to_xml(self, resource_fs):

        xml_object = etree.Element('randomize')
        for child in self.get_children():
            self.runtime.add_block_as_child_node(child, xml_object)
        return xml_object

    def has_dynamic_children(self):
        """
        Grading needs to know that only one of the children is actually "real".  This
        makes it use module.get_child_descriptors().
        """
        return True
