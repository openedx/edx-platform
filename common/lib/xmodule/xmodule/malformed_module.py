from pkg_resources import resource_string
from lxml import etree
from xmodule.mako_module import MakoModuleDescriptor
from xmodule.xml_module import XmlDescriptor
from xmodule.editing_module import EditingDescriptor

import logging

log = logging.getLogger(__name__)

class MalformedDescriptor(EditingDescriptor):
    """
    Module that provides a raw editing view of broken xml.
    """

    @classmethod
    def from_xml(cls, xml_data, system, org=None, course=None):
        '''Create an instance of this descriptor from the supplied data.

        Does not try to parse the data--just stores it.
        '''

        #log.debug("processing '{0}'".format(xml_data))
        try:
            xml_obj = etree.fromstring(xml_data)
            if xml_obj.tag == 'malformed':
                xml_data = xml_obj.text
            # TODO (vshnayder): how does one get back from this to a valid descriptor?
            # For now, have to fix manually.
        except etree.XMLSyntaxError:
            pass

        definition = { 'data' : xml_data }
        # TODO (vshnayder): Do we need a valid slug here?  Just pick a random
        # 64-bit num?
        location = ['i4x', org, course, 'malformed', 'slug']
        metadata = {}  # stays in the xml_data

        return cls(system, definition, location=location, metadata=metadata)

    def export_to_xml(self, resource_fs):
        '''
        Export as a string wrapped in xml
        '''
        root = etree.Element('malformed')
        root.text = self.definition['data']
        return etree.tostring(root)

