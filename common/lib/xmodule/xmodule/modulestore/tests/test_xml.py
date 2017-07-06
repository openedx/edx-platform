"""
Tests around our XML modulestore, including importing
well-formed and not-well-formed XML.
"""
import os.path
import unittest
from glob import glob
from mock import patch, Mock

from xmodule.modulestore.xml import XMLModuleStore
from xmodule.modulestore import ModuleStoreEnum
from xmodule.x_module import XModuleMixin

from xmodule.tests import DATA_DIR
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xmodule.modulestore.tests.test_modulestore import check_has_course_method


def glob_tildes_at_end(path):
    """
    A wrapper for the `glob.glob` function, but it always returns
    files that end in a tilde (~) at the end of the list of results.
    """
    result = glob(path)
    with_tildes = [f for f in result if f.endswith("~")]
    no_tildes = [f for f in result if not f.endswith("~")]
    return no_tildes + with_tildes


class TestXMLModuleStore(unittest.TestCase):
    """
    Test around the XML modulestore
    """
    @patch('xmodule.tabs.CourseTabList.initialize_default', Mock())
    def test_unicode_chars_in_xml_content(self):
        # edX/full/6.002_Spring_2012 has non-ASCII chars, and during
        # uniquification of names, would raise a UnicodeError. It no longer does.

        # Ensure that there really is a non-ASCII character in the course.
        with open(os.path.join(DATA_DIR, "toy/sequential/vertical_sequential.xml")) as xmlf:
            xml = xmlf.read()
            with self.assertRaises(UnicodeDecodeError):
                xml.decode('ascii')

        # Load the course, but don't make error modules.  This will succeed,
        # but will record the errors.
        modulestore = XMLModuleStore(
            DATA_DIR,
            source_dirs=['toy'],
            xblock_mixins=(XModuleMixin,),
            load_error_modules=False)

        # Look up the errors during load. There should be none.
        errors = modulestore.get_course_errors(SlashSeparatedCourseKey("edX", "toy", "2012_Fall"))
        assert errors == []

    @patch("xmodule.modulestore.xml.glob.glob", side_effect=glob_tildes_at_end)
    def test_tilde_files_ignored(self, _fake_glob):
        modulestore = XMLModuleStore(DATA_DIR, source_dirs=['tilde'], load_error_modules=False)
        about_location = SlashSeparatedCourseKey('edX', 'tilde', '2012_Fall').make_usage_key(
            'about', 'index',
        )
        about_module = modulestore.get_item(about_location)
        self.assertIn("GREEN", about_module.data)
        self.assertNotIn("RED", about_module.data)

    def test_get_courses_for_wiki(self):
        """
        Test the get_courses_for_wiki method
        """
        store = XMLModuleStore(DATA_DIR, source_dirs=['toy', 'simple'])
        for course in store.get_courses():
            course_locations = store.get_courses_for_wiki(course.wiki_slug)
            self.assertEqual(len(course_locations), 1)
            self.assertIn(course.location.course_key, course_locations)

        course_locations = store.get_courses_for_wiki('no_such_wiki')
        self.assertEqual(len(course_locations), 0)

        # now set toy course to share the wiki with simple course
        toy_course = store.get_course(SlashSeparatedCourseKey('edX', 'toy', '2012_Fall'))
        toy_course.wiki_slug = 'simple'

        course_locations = store.get_courses_for_wiki('toy')
        self.assertEqual(len(course_locations), 0)

        course_locations = store.get_courses_for_wiki('simple')
        self.assertEqual(len(course_locations), 2)
        for course_number in ['toy', 'simple']:
            self.assertIn(SlashSeparatedCourseKey('edX', course_number, '2012_Fall'), course_locations)

    def test_has_course(self):
        """
        Test the has_course method
        """
        check_has_course_method(
            XMLModuleStore(DATA_DIR, source_dirs=['toy', 'simple']),
            SlashSeparatedCourseKey('edX', 'toy', '2012_Fall'),
            locator_key_fields=SlashSeparatedCourseKey.KEY_FIELDS
        )

    def test_branch_setting(self):
        """
        Test the branch setting context manager
        """
        store = XMLModuleStore(DATA_DIR, source_dirs=['toy'])
        course = store.get_courses()[0]

        # XML store allows published_only branch setting
        with store.branch_setting(ModuleStoreEnum.Branch.published_only, course.id):
            store.get_item(course.location)

        # XML store does NOT allow draft_preferred branch setting
        with self.assertRaises(ValueError):
            with store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, course.id):
                # verify that the above context manager raises a ValueError
                pass  # pragma: no cover

    @patch('xmodule.modulestore.xml.log')
    def test_dag_course(self, mock_logging):
        """
        Test a course whose structure is not a tree.
        """
        store = XMLModuleStore(
            DATA_DIR,
            source_dirs=['xml_dag'],
            xblock_mixins=(XModuleMixin,),
        )
        course_key = store.get_courses()[0].id

        mock_logging.warning.assert_called_with(
            "%s has more than one definition", course_key.make_usage_key('discussion', 'duplicate_def')
        )

        shared_item_loc = course_key.make_usage_key('html', 'toyhtml')
        shared_item = store.get_item(shared_item_loc)
        parent = shared_item.get_parent()
        self.assertIsNotNone(parent, "get_parent failed to return a value")
        parent_loc = course_key.make_usage_key('vertical', 'vertical_test')
        self.assertEqual(parent.location, parent_loc)
        self.assertIn(shared_item, parent.get_children())
        # ensure it's still a child of the other parent even tho it doesn't claim the other parent as its parent
        other_parent_loc = course_key.make_usage_key('vertical', 'zeta')
        other_parent = store.get_item(other_parent_loc)
        # children rather than get_children b/c the instance returned by get_children != shared_item
        self.assertIn(shared_item_loc, other_parent.children)
