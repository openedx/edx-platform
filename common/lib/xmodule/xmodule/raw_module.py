from lxml import etree
from xmodule.editing_module import XMLEditingDescriptor
from xmodule.xml_module import XmlDescriptor
import logging
import sys

log = logging.getLogger(__name__)

class RawDescriptor(XmlDescriptor, XMLEditingDescriptor):
    """
    Module that provides a raw editing view of its data and children.  It
    requires that the definition xml is valid.
    """
    @classmethod
    def definition_from_xml(cls, xml_object, system):
        return {'data': etree.tostring(xml_object, pretty_print=True)}

    def definition_to_xml(self, resource_fs):
        try:
            return etree.fromstring(self.definition['data'])
        except etree.XMLSyntaxError as err:
            # Can't recover here, so just add some info and
            # re-raise
            lines = self.definition['data'].split('\n')
            line, offset = err.position
            msg = ("Unable to create xml for problem {loc}. "
                   "Context: '{context}'".format(
                    context=lines[line - 1][offset - 40:offset + 40],
                    loc=self.location))
            raise Exception, msg, sys.exc_info()[2]
