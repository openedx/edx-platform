from path import path
import unittest
from fs.memoryfs import MemoryFS

from lxml import etree

from xmodule.x_module import XMLParsingSystem, XModuleDescriptor
from xmodule.xml_module import is_pointer_tag
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
        '''Check that malformed xml loads as an ErrorDescriptor.'''

        bad_xml = '''<sequential display_name="oops"><video url="hi"></sequential>'''
        system = self.get_system()

        descriptor = XModuleDescriptor.load_from_xml(bad_xml, system, 'org', 'course',
                                                     None)

        self.assertEqual(descriptor.__class__.__name__,
                         'ErrorDescriptor')


    def test_unique_url_names(self):
        '''Check that each error gets its very own url_name'''
        bad_xml = '''<sequential display_name="oops"><video url="hi"></sequential>'''
        bad_xml2 = '''<sequential url_name="oops"><video url="hi"></sequential>'''
        system = self.get_system()

        descriptor1 = XModuleDescriptor.load_from_xml(bad_xml, system, 'org',
                                                      'course', None)

        descriptor2 = XModuleDescriptor.load_from_xml(bad_xml2, system, 'org',
                                                      'course', None)

        self.assertNotEqual(descriptor1.location, descriptor2.location)


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

    def test_metadata_import_export(self):
        """Two checks:
            - unknown metadata is preserved across import-export
            - inherited metadata doesn't leak to children.
        """
        system = self.get_system()
        v = '1 hour'
        org = 'foo'
        course = 'bbhh'
        url_name = 'test1'
        start_xml = '''
        <course org="{org}" course="{course}"
                graceperiod="{grace}" url_name="{url_name}" unicorn="purple">
            <chapter url="hi" url_name="ch" display_name="CH">
                <html url_name="h" display_name="H">Two houses, ...</html>
            </chapter>
        </course>'''.format(grace=v, org=org, course=course, url_name=url_name)
        descriptor = XModuleDescriptor.load_from_xml(start_xml, system,
                                                     org, course)

        print descriptor, descriptor.metadata
        self.assertEqual(descriptor.metadata['graceperiod'], v)
        self.assertEqual(descriptor.metadata['unicorn'], 'purple')

        # Check that the child inherits graceperiod correctly
        child = descriptor.get_children()[0]
        self.assertEqual(child.metadata['graceperiod'], v)

        # check that the child does _not_ inherit any unicorns
        self.assertTrue('unicorn' not in child.metadata)

        # Now export and check things
        resource_fs = MemoryFS()
        exported_xml = descriptor.export_to_xml(resource_fs)

        # Check that the exported xml is just a pointer
        print "Exported xml:", exported_xml
        pointer = etree.fromstring(exported_xml)
        self.assertTrue(is_pointer_tag(pointer))
        # but it's a special case course pointer
        self.assertEqual(pointer.attrib['course'], course)
        self.assertEqual(pointer.attrib['org'], org)

        # Does the course still have unicorns?
        with resource_fs.open('course/{url_name}.xml'.format(url_name=url_name)) as f:
            course_xml = etree.fromstring(f.read())

        self.assertEqual(course_xml.attrib['unicorn'], 'purple')

        # the course and org tags should be _only_ in the pointer
        self.assertTrue('course' not in course_xml.attrib)
        self.assertTrue('org' not in course_xml.attrib)

        # did we successfully strip the url_name from the definition contents?
        self.assertTrue('url_name' not in course_xml.attrib)

        # Does the chapter tag now have a graceperiod attribute?
        # hardcoded path to child
        with resource_fs.open('chapter/ch.xml') as f:
            chapter_xml = etree.fromstring(f.read())
        self.assertEqual(chapter_xml.tag, 'chapter')
        self.assertFalse('graceperiod' in chapter_xml.attrib)
