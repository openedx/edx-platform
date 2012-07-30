from pkg_resources import resource_string
from lxml import etree
from xmodule.x_module import XModule
from xmodule.mako_module import MakoModuleDescriptor
from xmodule.xml_module import XmlDescriptor
from xmodule.editing_module import EditingDescriptor

import logging

log = logging.getLogger(__name__)

class MalformedModule(XModule):
    def get_html(self):
        '''Show an error.
        TODO (vshnayder): proper style, divs, etc.
        '''
        return "Malformed content--not showing through get_html()"

class MalformedDescriptor(EditingDescriptor):
    """
    Module that provides a raw editing view of broken xml.
    """
    module_class = MalformedModule

    @classmethod
    def from_xml(cls, xml_data, system, org=None, course=None):
        '''Create an instance of this descriptor from the supplied data.

        Does not try to parse the data--just stores it.
        '''

        try:
            # If this is already a malformed tag, don't want to re-wrap it.
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
        If the definition data is invalid xml, export it wrapped in a malformed
        tag.  If it is valid, export without the wrapper.

        NOTE: There may still be problems with the valid xml--it could be
        missing required attributes, could have the wrong tags, refer to missing
        files, etc.
        '''
        try:
           xml = etree.fromstring(self.definition['data'])
           return etree.tostring(xml)
        except etree.XMLSyntaxError:
            # still not valid.
            root = etree.Element('malformed')
            root.text = self.definition['data']
            return etree.tostring(root)
