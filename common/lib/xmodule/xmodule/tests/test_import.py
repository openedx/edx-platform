from path import path
import unittest
from fs.memoryfs import MemoryFS

from lxml import etree

from xmodule.x_module import XMLParsingSystem, XModuleDescriptor
from xmodule.xml_module import is_pointer_tag
from xmodule.errortracker import make_error_tracker
from xmodule.modulestore import Location
from xmodule.modulestore.xml import XMLModuleStore
from xmodule.modulestore.exceptions import ItemNotFoundError

from .test_export import DATA_DIR

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

        policy = {}
        XMLParsingSystem.__init__(self, load_item, self.resources_fs,
                                  self.errorlog.tracker, process_xml, policy)

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

    def test_metadata_inherit(self):
        """Make sure that metadata is inherited properly"""

        print "Starting import"
        initial_import = XMLModuleStore(DATA_DIR, course_dirs=['toy'])

        courses = initial_import.get_courses()
        self.assertEquals(len(courses), 1)
        course = courses[0]

        def check_for_key(key, node):
            "recursive check for presence of key"
            print "Checking {0}".format(node.location.url())
            self.assertTrue(key in node.metadata)
            for c in node.get_children():
                check_for_key(key, c)

        check_for_key('graceperiod', course)


    def test_policy_loading(self):
        """Make sure that when two courses share content with the same
        org and course names, policy applies to the right one."""

        def get_course(name):
            print "Importing {0}".format(name)

            modulestore = XMLModuleStore(DATA_DIR, course_dirs=[name])
            courses = modulestore.get_courses()
            self.assertEquals(len(courses), 1)
            return courses[0]

        toy = get_course('toy')
        two_toys = get_course('two_toys')

        self.assertEqual(toy.url_name, "2012_Fall")
        self.assertEqual(two_toys.url_name, "TT_2012_Fall")

        toy_ch = toy.get_children()[0]
        two_toys_ch = two_toys.get_children()[0]

        self.assertEqual(toy_ch.display_name, "Overview")
        self.assertEqual(two_toys_ch.display_name, "Two Toy Overview")

        # Also check that the grading policy loaded
        self.assertEqual(two_toys.grade_cutoffs['C'], 0.5999)

        # Also check that keys from policy are run through the
        # appropriate attribute maps -- 'graded' should be True, not 'true'
        self.assertEqual(toy.metadata['graded'], True)


    def test_definition_loading(self):
        """When two courses share the same org and course name and
        both have a module with the same url_name, the definitions shouldn't clash.

        TODO (vshnayder): once we have a CMS, this shouldn't
        happen--locations should uniquely name definitions.  But in
        our imperfect XML world, it can (and likely will) happen."""

        modulestore = XMLModuleStore(DATA_DIR, course_dirs=['toy', 'two_toys'])

        toy_id = "edX/toy/2012_Fall"
        two_toy_id = "edX/toy/TT_2012_Fall"

        location = Location(["i4x", "edX", "toy", "video", "Welcome"])
        toy_video = modulestore.get_instance(toy_id, location)
        two_toy_video =  modulestore.get_instance(two_toy_id, location)
        self.assertEqual(toy_video.metadata['youtube'], "1.0:p2Q6BrNhdh8")
        self.assertEqual(two_toy_video.metadata['youtube'], "1.0:p2Q6BrNhdh9")


    def test_colon_in_url_name(self):
        """Ensure that colons in url_names convert to file paths properly"""

        print "Starting import"
        modulestore = XMLModuleStore(DATA_DIR, course_dirs=['toy'])

        courses = modulestore.get_courses()
        self.assertEquals(len(courses), 1)
        course = courses[0]
        course_id = course.id

        print "course errors:"
        for (msg, err) in modulestore.get_item_errors(course.location):
            print msg
            print err

        chapters = course.get_children()
        self.assertEquals(len(chapters), 2)

        ch2 = chapters[1]
        self.assertEquals(ch2.url_name, "secret:magic")

        print "Ch2 location: ", ch2.location

        also_ch2 = modulestore.get_instance(course_id, ch2.location)
        self.assertEquals(ch2, also_ch2)

        print "making sure html loaded"
        cloc = course.location
        loc = Location(cloc.tag, cloc.org, cloc.course, 'html', 'secret:toylab')
        html = modulestore.get_instance(course_id, loc)
        self.assertEquals(html.display_name, "Toy lab")

    def test_url_name_mangling(self):
        """
        Make sure that url_names are only mangled once.
        """

        modulestore = XMLModuleStore(DATA_DIR, course_dirs=['toy'])

        toy_id = "edX/toy/2012_Fall"

        course = modulestore.get_courses()[0]
        chapters = course.get_children()
        ch1 = chapters[0]
        sections = ch1.get_children()

        self.assertEqual(len(sections), 4)

        for i in (2,3):
            video = sections[i]
            # Name should be 'video_{hash}'
            print "video {0} url_name: {1}".format(i, video.url_name)

            self.assertEqual(len(video.url_name), len('video_') + 12)

