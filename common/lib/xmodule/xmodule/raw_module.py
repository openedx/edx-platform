from lxml import etree
from xmodule.editing_module import XMLEditingDescriptor
from xmodule.xml_module import XmlDescriptor
import logging
from xblock.fields import String, Scope
from exceptions import SerializationError

log = logging.getLogger(__name__)


class RawDescriptor(XmlDescriptor, XMLEditingDescriptor):
    """
    Module that provides a raw editing view of its data and children.  It
    requires that the definition xml is valid.
    """
    data = String(help="XML data for the module", default="", scope=Scope.content)

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        # because we repeatedly copy and convert the xml, this is the only sure
        # place to remove these attrs if they exist
        for attr in ['parent_url', 'parent_sequential_url', 'index_in_children_list']:
            if attr in xml_object.attrib:
                del xml_object.attrib[attr]
        return {'data': etree.tostring(xml_object, pretty_print=True, encoding='unicode')}, []

    def definition_to_xml(self, resource_fs):
        try:
            return etree.fromstring(self.data)
        except etree.XMLSyntaxError as err:
            # Can't recover here, so just add some info and
            # re-raise
            lines = self.data.split('\n')
            line, offset = err.position
            msg = (
                u"Unable to create xml for module {loc}. "
                u"Context: '{context}'"
            ).format(
                context=lines[line - 1][offset - 40:offset + 40],
                loc=self.location,
            )
            raise SerializationError(self.location, msg)


class EmptyDataRawDescriptor(XmlDescriptor, XMLEditingDescriptor):
    """
    Version of RawDescriptor for modules which may have no XML data,
    but use XMLEditingDescriptor for import/export handling.
    """
    data = String(default='', scope=Scope.content)

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        if len(xml_object) == 0 and len(xml_object.items()) == 0:
            return {'data': ''}, []
        return {'data': etree.tostring(xml_object, pretty_print=True, encoding='unicode')}, []

    def definition_to_xml(self, resource_fs):
        if self.data:
            return etree.fromstring(self.data)
        return etree.Element(self.category)
