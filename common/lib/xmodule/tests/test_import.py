from path import path

import unittest

from xmodule.x_module import XMLParsingSystem, XModuleDescriptor
from xmodule.errorhandlers import ignore_errors_handler
from xmodule.modulestore import Location

class ImportTestCase(unittest.TestCase):
    '''Make sure module imports work properly, including for malformed inputs'''

    def test_fallback(self):
        '''Make sure that malformed xml loads as a MalformedDescriptorb.'''

        bad_xml = '''<sequential display_name="oops"><video url="hi"></sequential>'''

        # Shouldn't need any system params, because the initial parse should fail
        def load_item(loc):
            raise Exception("Shouldn't be called")

        resources_fs = None

        def process_xml(xml):
            raise Exception("Shouldn't be called")


        def render_template(template, context):
            raise Exception("Shouldn't be called")

        system = XMLParsingSystem(load_item, resources_fs,
                                  ignore_errors_handler, process_xml)
        system.render_template = render_template

        descriptor = XModuleDescriptor.load_from_xml(bad_xml, system, 'org', 'course',
                                                     None)

        self.assertEqual(descriptor.__class__.__name__,
                         'MalformedDescriptor')
