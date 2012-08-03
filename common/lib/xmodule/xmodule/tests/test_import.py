from path import path
import unittest
from fs.memoryfs import MemoryFS

from lxml import etree

from xmodule.x_module import XMLParsingSystem, XModuleDescriptor
from xmodule.errortracker import make_error_tracker
from xmodule.modulestore import Location
from xmodule.modulestore.exceptions import ItemNotFoundError

ORG = 'test_org'
COURSE = 'test_course'

class DummySystem(XMLParsingSystem):
    def __init__(self):

        self.modules = {}
        self.resources_fs = MemoryFS()
        self.errorlog = make_error_tracker()

        def load_item(loc):
            loc = Location(loc)
            if loc in self.modules:
                return self.modules[loc]

            print "modules: "
            print self.modules
            raise ItemNotFoundError("Can't find item at loc: {0}".format(loc))

        def process_xml(xml):
            print "loading {0}".format(xml)
            descriptor = XModuleDescriptor.load_from_xml(xml, self, ORG, COURSE, None)
            # Need to save module so we can find it later
            self.modules[descriptor.location] = descriptor

            # always eager
            descriptor.get_children()
            return descriptor


        XMLParsingSystem.__init__(self, load_item, self.resources_fs,
                                  self.errorlog.tracker, process_xml)

    def render_template(self, template, context):
            raise Exception("Shouldn't be called")




class ImportTestCase(unittest.TestCase):
    '''Make sure module imports work properly, including for malformed inputs'''


    @staticmethod
    def get_system():
        '''Get a dummy system'''
        return DummySystem()

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

        self.maxDiff = None
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

    def test_metadata_inherit(self):
        """Make sure metadata inherits properly"""
        system = self.get_system()
        v = "1 hour"
        start_xml = '''<course graceperiod="{grace}" url_name="test1" display_name="myseq">
                      <chapter url="hi" url_name="ch" display_name="CH">
                       <html url_name="h" display_name="H">Two houses, ...</html></chapter>
                   </course>'''.format(grace=v)
        descriptor = XModuleDescriptor.load_from_xml(start_xml, system,
                                                     'org', 'course')

        print "Errors: {0}".format(system.errorlog.errors)
        print descriptor, descriptor.metadata
        self.assertEqual(descriptor.metadata['graceperiod'], v)

        # Check that the child inherits correctly
        child = descriptor.get_children()[0]
        self.assertEqual(child.metadata['graceperiod'], v)

        # Now export and see if the chapter tag has a graceperiod attribute
        resource_fs = MemoryFS()
        exported_xml = descriptor.export_to_xml(resource_fs)
        print "Exported xml:", exported_xml
        # hardcode path to child
        with resource_fs.open('chapter/ch.xml') as f:
            chapter_xml = etree.fromstring(f.read())
        self.assertEqual(chapter_xml.tag, 'chapter')
        self.assertFalse('graceperiod' in chapter_xml.attrib)
