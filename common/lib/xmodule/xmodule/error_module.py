from pkg_resources import resource_string
from lxml import etree
from xmodule.x_module import XModule
from xmodule.mako_module import MakoModuleDescriptor
from xmodule.xml_module import XmlDescriptor
from xmodule.editing_module import EditingDescriptor

import logging

log = logging.getLogger(__name__)

class ErrorModule(XModule):
    def get_html(self):
        '''Show an error.
        TODO (vshnayder): proper style, divs, etc.
        '''
        if not self.system.is_staff:
            return self.system.render_template('module-error.html', {})

        # staff get to see all the details
        return self.system.render_template('module-error-staff.html', {
            'data' : self.definition['data'],
            # TODO (vshnayder): need to get non-syntax errors in here somehow
            'error' : self.definition.get('error', 'Error not available')
            })

class ErrorDescriptor(EditingDescriptor):
    """
    Module that provides a raw editing view of broken xml.
    """
    module_class = ErrorModule

    @classmethod
    def from_xml(cls, xml_data, system, org=None, course=None, err=None):
        '''Create an instance of this descriptor from the supplied data.

        Does not try to parse the data--just stores it.

        Takes an extra, optional, parameter--the error that caused an
        issue.
        '''

        definition = {}
        if err is not None:
            definition['error'] = err

        try:
            # If this is already an error tag, don't want to re-wrap it.
            xml_obj = etree.fromstring(xml_data)
            if xml_obj.tag == 'error':
                xml_data = xml_obj.text
        except etree.XMLSyntaxError as err:
            # Save the error to display later--overrides other problems
            definition['error'] = err

        definition['data'] = xml_data
        # TODO (vshnayder): Do we need a unique slug here?  Just pick a random
        # 64-bit num?
        location = ['i4x', org, course, 'error', 'slug']
        metadata = {}  # stays in the xml_data

        return cls(system, definition, location=location, metadata=metadata)

    def export_to_xml(self, resource_fs):
        '''
        If the definition data is invalid xml, export it wrapped in an "error"
        tag.  If it is valid, export without the wrapper.

        NOTE: There may still be problems with the valid xml--it could be
        missing required attributes, could have the wrong tags, refer to missing
        files, etc.  That would just get re-wrapped on import.
        '''
        try:
           xml = etree.fromstring(self.definition['data'])
           return etree.tostring(xml)
        except etree.XMLSyntaxError:
            # still not valid.
            root = etree.Element('error')
            root.text = self.definition['data']
            return etree.tostring(root)
