import unittest

from fs.osfs import OSFS
from nose.tools import assert_equals, assert_true
from path import path
from tempfile import mkdtemp

from xmodule.modulestore.xml import XMLModuleStore

# from ~/mitx_all/mitx/common/lib/xmodule/xmodule/tests/
# to   ~/mitx_all/mitx/common/test
TEST_DIR = path(__file__).abspath().dirname()
for i in range(4):
    TEST_DIR = TEST_DIR.dirname()
TEST_DIR = TEST_DIR / 'test'

DATA_DIR = TEST_DIR / 'data'


def strip_metadata(descriptor, key):
    """
    Recursively strips tag from all children.
    """
    print "strip {key} from {desc}".format(key=key, desc=descriptor.location.url())
    descriptor.metadata.pop(key, None)
    for d in descriptor.get_children():
        strip_metadata(d, key)

def check_gone(descriptor, key):
    '''Make sure that the metadata of this descriptor or any
    descendants does not include key'''
    assert_true(key not in descriptor.metadata)
    for d in descriptor.get_children():
        check_gone(d, key)



class RoundTripTestCase(unittest.TestCase):
    '''Check that our test courses roundtrip properly'''
    def check_export_roundtrip(self, data_dir, course_dir):
        print "Starting import"
        initial_import = XMLModuleStore(data_dir, eager=True, course_dirs=[course_dir])

        courses = initial_import.get_courses()
        self.assertEquals(len(courses), 1)
        initial_course = courses[0]

        print "Starting export"
        export_dir = mkdtemp()
        print "export_dir: {0}".format(export_dir)
        fs = OSFS(export_dir)
        export_course_dir = 'export'
        export_fs = fs.makeopendir(export_course_dir)

        xml = initial_course.export_to_xml(export_fs)
        with export_fs.open('course.xml', 'w') as course_xml:
            course_xml.write(xml)

        print "Starting second import"
        second_import = XMLModuleStore(export_dir, eager=True,
                                       course_dirs=[export_course_dir])

        courses2 = second_import.get_courses()
        self.assertEquals(len(courses2), 1)
        exported_course = courses2[0]

        print "Checking course equality"
        # HACK: data_dir metadata tags break equality because they
        # aren't real metadata, and depend on paths. Remove them.
        strip_metadata(initial_course, 'data_dir')
        strip_metadata(exported_course, 'data_dir')

        self.assertEquals(initial_course, exported_course)

        print "Checking key equality"
        self.assertEquals(sorted(initial_import.modules.keys()),
                          sorted(second_import.modules.keys()))

        print "Checking module equality"
        for location in initial_import.modules.keys():
            print "Checking", location
            if location.category == 'html':
                print ("Skipping html modules--they can't import in"
                       " final form without writing files...")
                continue
            self.assertEquals(initial_import.modules[location],
                              second_import.modules[location])


    def setUp(self):
        self.maxDiff = None

    def test_toy_roundtrip(self):
        self.check_export_roundtrip(DATA_DIR, "toy")

    def test_simple_roundtrip(self):
        self.check_export_roundtrip(DATA_DIR, "simple")

    def test_full_roundtrip(self):
        self.check_export_roundtrip(DATA_DIR, "full")
