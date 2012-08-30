import unittest

from fs.osfs import OSFS
from nose.tools import assert_equals, assert_true
from path import path
from tempfile import mkdtemp
from shutil import copytree

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

def strip_filenames(descriptor):
    """
    Recursively strips 'filename' from all children's definitions.
    """
    print "strip filename from {desc}".format(desc=descriptor.location.url())
    descriptor.definition.pop('filename', None)
    for d in descriptor.get_children():
        strip_filenames(d)



class RoundTripTestCase(unittest.TestCase):
    '''Check that our test courses roundtrip properly'''
    def check_export_roundtrip(self, data_dir, course_dir):

        root_dir = path(mkdtemp())
        print "Copying test course to temp dir {0}".format(root_dir)

        data_dir = path(data_dir)
        copytree(data_dir / course_dir, root_dir / course_dir)

        print "Starting import"
        initial_import = XMLModuleStore(root_dir, course_dirs=[course_dir])

        courses = initial_import.get_courses()
        self.assertEquals(len(courses), 1)
        initial_course = courses[0]

        # export to the same directory--that way things like the custom_tags/ folder
        # will still be there.
        print "Starting export"
        fs = OSFS(root_dir)
        export_fs = fs.makeopendir(course_dir)

        xml = initial_course.export_to_xml(export_fs)
        with export_fs.open('course.xml', 'w') as course_xml:
            course_xml.write(xml)

        print "Starting second import"
        second_import = XMLModuleStore(root_dir, course_dirs=[course_dir])

        courses2 = second_import.get_courses()
        self.assertEquals(len(courses2), 1)
        exported_course = courses2[0]

        print "Checking course equality"
        # HACK: data_dir metadata tags break equality because they
        # aren't real metadata, and depend on paths. Remove them.
        strip_metadata(initial_course, 'data_dir')
        strip_metadata(exported_course, 'data_dir')

        # HACK: filenames change when changing file formats
        # during imports from old-style courses.  Ignore them.
        strip_filenames(initial_course)
        strip_filenames(exported_course)

        self.assertEquals(initial_course, exported_course)
        self.assertEquals(initial_course.id, exported_course.id)
        course_id = initial_course.id

        print "Checking key equality"
        self.assertEquals(sorted(initial_import.modules[course_id].keys()),
                          sorted(second_import.modules[course_id].keys()))

        print "Checking module equality"
        for location in initial_import.modules[course_id].keys():
            print "Checking", location
            if location.category == 'html':
                print ("Skipping html modules--they can't import in"
                       " final form without writing files...")
                continue
            self.assertEquals(initial_import.modules[course_id][location],
                              second_import.modules[course_id][location])


    def setUp(self):
        self.maxDiff = None

    def test_toy_roundtrip(self):
        self.check_export_roundtrip(DATA_DIR, "toy")

    def test_simple_roundtrip(self):
        self.check_export_roundtrip(DATA_DIR, "simple")

    def test_full_roundtrip(self):
        self.check_export_roundtrip(DATA_DIR, "full")
