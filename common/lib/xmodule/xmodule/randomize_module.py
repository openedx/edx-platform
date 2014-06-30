import json
import logging
import random

from xmodule.x_module import XModule
from xmodule.seq_module import SequenceDescriptor

from lxml import etree

from xblock.fields import Scope, Integer
from xblock.fragment import Fragment

log = logging.getLogger('edx.' + __name__)


class RandomizeFields(object):
    choice = Integer(help="Which random child was chosen",
                     scope=Scope.user_state)


class RandomizeModule(RandomizeFields, XModule):
    """
    Chooses a random child module. Chooses the same one every time for each
    student.

     Example:
     <randomize>
     <problem url_name="problem1" />
     <problem url_name="problem2" />
     <problem url_name="problem3" />
     </randomize>

    User notes:
      - If you're randomizing amongst graded modules, each of them MUST be
        worth the same number of points. Otherwise, the earth will be overrun
        by monsters from the deeps. You have been warned.

    Technical notes:
      - There is more dark magic in this code than I'd like. The whole
        varying-children + grading interaction is a tangle between super and
        subclasses of descriptors and modules.
    """
    def __init__(self, *args, **kwargs):
        super(RandomizeModule, self).__init__(*args, **kwargs)
        # NOTE: calling self.get_children() creates a circular reference --
        # it calls get_child_descriptors() internally, but that doesn't work
        # until we've picked a choice
        # import pudb; pudb.set_trace()
        children = self.descriptor.get_children()
        xml_attrs = self.descriptor.xml_attributes or []
        use_randrange = 'use_randrange' in xml_attrs
        # TODO: use this attr to toggle storing history and never showing the
        # same problem twice
        # no_repeats = xml_attrs.has_key('no_repeats')
        num_choices = len(children)

        if self.choice > num_choices:
            # Oops.  Children changed. Reset.
            self.choice = None

        if self.choice is None:
            # choose one based on the system seed, or randomly if that's not
            # available
            if num_choices > 0:
                if self.system.seed is not None and not use_randrange:
                    self.choice = self.system.seed % num_choices
                    log.debug('using seed for %s choice=%s' %
                              (str(self.location), self.choice))
                else:
                    self.choice = random.randrange(0, num_choices)
                    log.debug('using randrange for %s' % str(self.location))
            else:
                log.debug('error in randomize: num_choices = %s' % num_choices)

        if self.choice is not None:
            self.child_descriptor = self.descriptor.get_children()[self.choice]
            # Now get_children() should return a list with one element
            log.debug("choice=%s in %s, children of randomize module "
                      "(should be only 1): %s", self.choice,
                      str(self.location), self.get_children())
            self.child = self.get_children()[0]
        else:
            self.child_descriptor = None
            self.child = None

    def get_child_descriptors(self):
        """
        For grading--return just the chosen child.
        """
        if self.child_descriptor is None:
            return []
        return [self.child_descriptor]

    def student_view(self, context):
        if self.child is None:
            # raise error instead?  In fact, could complain on descriptor load
            return Fragment(content=u"<div>Nothing to randomize between</div>")
        child_html = self.child.render('student_view', context)
        if self.system.user_is_staff:
            dishtml = self.system.render_template('randomize_control.html', {
                'element_id': self.location.html_id(),
                'is_staff': self.system.user_is_staff,
                'ajax_url': self.system.ajax_url,
                'choice': self.choice,
                'num_choices': len(self.descriptor.get_children()),
            })
            # html = '<html><p>Welcome, staff.  Randomize loc=%s ;
            # Choice=%s</p><br/><hr/></br/>' % (str(self.location),
            # self.choice)
            return Fragment(u"<html>" + dishtml + child_html.content +
                            u"</html>")
        return child_html

    def handle_ajax(self, dispatch, data):
        if dispatch == 'next':
            self.choice = self.choice + 1
        elif dispatch == 'jump':
            log.debug('jump, data=%s' % data)
            self.choice = int(data['choice'])
        num_choices = len(self.descriptor.get_children())
        if self.choice >= num_choices:
            self.choice = 0

        result = {'ret': "choice=%s" % self.choice}
        return json.dumps(result)

    def get_icon_class(self):
        return self.child.get_icon_class() if self.child else 'other'


class RandomizeDescriptor(RandomizeFields, SequenceDescriptor):
    # the editing interface can be the same as for sequences -- just a
    # container
    module_class = RandomizeModule
    filename_extension = "xml"

    def definition_to_xml(self, resource_fs):
        xml_object = etree.Element('randomize')
        for child in self.get_children():
            self.runtime.add_block_as_child_node(child, xml_object)
        return xml_object

    def has_dynamic_children(self):
        """
        Grading needs to know that only one of the children is actually "real".
        This makes it use module.get_child_descriptors().
        """
        return True
