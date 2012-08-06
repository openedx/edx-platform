import logging
import random
import string
import sys

from pkg_resources import resource_string
from lxml import etree
from xmodule.x_module import XModule
from xmodule.mako_module import MakoModuleDescriptor
from xmodule.xml_module import XmlDescriptor
from xmodule.editing_module import EditingDescriptor
from xmodule.errortracker import exc_info_to_str


log = logging.getLogger(__name__)

class ErrorModule(XModule):
    def get_html(self):
        '''Show an error.
        TODO (vshnayder): proper style, divs, etc.
        '''
        # staff get to see all the details
        return self.system.render_template('module-error.html', {
            'data' : self.definition['data']['contents'],
            'error' : self.definition['data']['error_msg'],
            'is_staff' : self.system.is_staff,
            })

class ErrorDescriptor(EditingDescriptor):
    """
    Module that provides a raw editing view of broken xml.
    """
    module_class = ErrorModule

    @classmethod
    def from_xml(cls, xml_data, system, org=None, course=None,
                 error_msg='Error not available'):
        '''Create an instance of this descriptor from the supplied data.

        Does not require that xml_data be parseable--just stores it and exports
        as-is if not.

        Takes an extra, optional, parameter--the error that caused an
        issue.  (should be a string, or convert usefully into one).
        '''
        # Use a nested inner dictionary because 'data' is hardcoded
        inner = {}
        definition = {'data': inner}
        inner['error_msg'] = str(error_msg)

        # Pick a unique (random) url_name.
        # NOTE: We could try to pull out the url_name of the errored descriptor,
        # but url_names aren't guaranteed to be unique between descriptor types,
        # and ErrorDescriptor can wrap any type.  When the wrapped module is fixed,
        # it will be written out with the original url_name.
        chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
        url_name = ''.join(random.choice(chars) for i in range(16))

        try:
            # If this is already an error tag, don't want to re-wrap it.
            xml_obj = etree.fromstring(xml_data)
            if xml_obj.tag == 'error':
                xml_data = xml_obj.text
                error_node = xml_obj.find('error_msg')
                if error_node is not None:
                    inner['error_msg'] = error_node.text
                else:
                    inner['error_msg'] = 'Error not available'

        except etree.XMLSyntaxError:
            # Save the error to display later--overrides other problems
            inner['error_msg'] = exc_info_to_str(sys.exc_info())

        inner['contents'] = xml_data
        # TODO (vshnayder): Do we need a unique slug here?  Just pick a random
        # 64-bit num?
        location = ['i4x', org, course, 'error', url_name]
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
           xml = etree.fromstring(self.definition['data']['contents'])
           return etree.tostring(xml)
        except etree.XMLSyntaxError:
            # still not valid.
            root = etree.Element('error')
            root.text = self.definition['data']['contents']
            err_node = etree.SubElement(root, 'error_msg')
            err_node.text = self.definition['data']['error_msg']
            return etree.tostring(root)
