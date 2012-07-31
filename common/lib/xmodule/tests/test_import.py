from path import path
import unittest

from lxml import etree

from xmodule.x_module import XMLParsingSystem, XModuleDescriptor
from xmodule.errortracker import null_error_tracker
from xmodule.modulestore import Location

class ImportTestCase(unittest.TestCase):
    '''Make sure module imports work properly, including for malformed inputs'''

    @staticmethod
    def get_system():
        '''Get a dummy system'''
        # Shouldn't need any system params, because the initial parse should fail
        def load_item(loc):
            raise Exception("Shouldn't be called")

        resources_fs = None

        def process_xml(xml):
            raise Exception("Shouldn't be called")


        def render_template(template, context):
            raise Exception("Shouldn't be called")

        system = XMLParsingSystem(load_item, resources_fs,
                                  null_error_tracker, process_xml)
        system.render_template = render_template

        return system

    def test_fallback(self):
        '''Make sure that malformed xml loads as an ErrorDescriptor.'''

        bad_xml = '''<sequential display_name="oops"><video url="hi"></sequential>'''

        system = self.get_system()

        descriptor = XModuleDescriptor.load_from_xml(bad_xml, system, 'org', 'course',
                                                     None)

        self.assertEqual(descriptor.__class__.__name__,
                         'ErrorDescriptor')

    def test_reimport(self):
        '''Make sure an already-exported error xml tag loads properly'''

        bad_xml = '''<sequential display_name="oops"><video url="hi"></sequential>'''
        system = self.get_system()
        descriptor = XModuleDescriptor.load_from_xml(bad_xml, system, 'org', 'course',
                                                     None)
        resource_fs = None
        tag_xml = descriptor.export_to_xml(resource_fs)
        re_import_descriptor = XModuleDescriptor.load_from_xml(tag_xml, system,
                                                               'org', 'course',
                                                               None)
        self.assertEqual(re_import_descriptor.__class__.__name__,
                         'ErrorDescriptor')

        self.assertEqual(descriptor.definition['data'],
                         re_import_descriptor.definition['data'])

    def test_fixed_xml_tag(self):
        """Make sure a tag that's been fixed exports as the original tag type"""

        # create a error tag with valid xml contents
        root = etree.Element('error')
        good_xml = '''<sequential display_name="fixed"><video url="hi"/></sequential>'''
        root.text = good_xml

        xml_str_in = etree.tostring(root)

        # load it
        system = self.get_system()
        descriptor = XModuleDescriptor.load_from_xml(xml_str_in, system, 'org', 'course',
                                                     None)
        # export it
        resource_fs = None
        xml_str_out = descriptor.export_to_xml(resource_fs)

        # Now make sure the exported xml is a sequential
        xml_out = etree.fromstring(xml_str_out)
        self.assertEqual(xml_out.tag, 'sequential')

