import os.path

from nose.tools import assert_raises, assert_equals  # pylint: disable=E0611

from xmodule.course_module import CourseDescriptor
from xmodule.modulestore.xml import XMLModuleStore
from xmodule.modulestore import XML_MODULESTORE_TYPE

from .test_modulestore import check_path_to_location
from xmodule.tests import DATA_DIR


class TestXMLModuleStore(object):
    def test_path_to_location(self):
        """Make sure that path_to_location works properly"""

        print "Starting import"
        modulestore = XMLModuleStore(DATA_DIR, course_dirs=['toy', 'simple'])
        print "finished import"

        check_path_to_location(modulestore)

    def test_xml_modulestore_type(self):
        store = XMLModuleStore(DATA_DIR, course_dirs=['toy', 'simple'])
        assert_equals(store.get_modulestore_type('foo/bar/baz'), XML_MODULESTORE_TYPE)

    def test_unicode_chars_in_xml_content(self):
        # edX/full/6.002_Spring_2012 has non-ASCII chars, and during
        # uniquification of names, would raise a UnicodeError. It no longer does.

        # Ensure that there really is a non-ASCII character in the course.
        with open(os.path.join(DATA_DIR, "toy/sequential/vertical_sequential.xml")) as xmlf:
            xml = xmlf.read()
            with assert_raises(UnicodeDecodeError):
                xml.decode('ascii')

        # Load the course, but don't make error modules.  This will succeed,
        # but will record the errors.
        modulestore = XMLModuleStore(DATA_DIR, course_dirs=['toy'], load_error_modules=False)

        # Look up the errors during load. There should be none.
        location = CourseDescriptor.id_to_location("edX/toy/2012_Fall")
        errors = modulestore.get_item_errors(location)
        assert errors == []
