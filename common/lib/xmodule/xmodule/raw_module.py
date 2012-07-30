from pkg_resources import resource_string
from lxml import etree
from xmodule.editing_module import EditingDescriptor
from xmodule.mako_module import MakoModuleDescriptor
from xmodule.xml_module import XmlDescriptor
import logging

log = logging.getLogger(__name__)

class RawDescriptor(XmlDescriptor, EditingDescriptor):
    """
    Module that provides a raw editing view of its data and children.  It
    requires that the definition xml is valid.
    """
    @classmethod
    def definition_from_xml(cls, xml_object, system):
        return {'data': etree.tostring(xml_object)}

    def definition_to_xml(self, resource_fs):
        try:
            return etree.fromstring(self.definition['data'])
        except etree.XMLSyntaxError as err:
            lines = self.definition['data'].split('\n')
            line, offset = err.position
            msg = ("Unable to create xml for problem {loc}. "
                   "Context: '{context}'".format(
                    context=lines[line - 1][offset - 40:offset + 40],
                    loc=self.location))
            log.exception(msg)
            self.system.error_handler(msg)
            # no workaround possible, so just re-raise
            raise
