"""
Tests that check that we ignore the appropriate files when importing courses.
"""
import unittest
from mock import Mock
from xmodule.modulestore.xml_importer import StaticContentImporter
from opaque_keys.edx.locator import CourseLocator
from xmodule.tests import DATA_DIR


class IgnoredFilesTestCase(unittest.TestCase):
    "Tests for ignored files"
    def test_ignore_tilde_static_files(self):
        course_dir = DATA_DIR / "tilde"
        course_id = CourseLocator("edX", "tilde", "Fall_2012")
        content_store = Mock()
        content_store.generate_thumbnail.return_value = ("content", "location")
        static_content_importer = StaticContentImporter(
            static_content_store=content_store,
            course_data_path=course_dir,
            target_id=course_id
        )
        static_content_importer.import_static_content_directory()
        saved_static_content = [call[0][0] for call in content_store.save.call_args_list]
        name_val = {sc.name: sc.data for sc in saved_static_content}
        self.assertIn("example.txt", name_val)
        self.assertNotIn("example.txt~", name_val)
        self.assertIn("GREEN", name_val["example.txt"])

    def test_ignore_dot_underscore_static_files(self):
        """
        Test for ignored Mac OS metadata files (filename starts with "._")
        """
        course_dir = DATA_DIR / "dot-underscore"
        course_id = CourseLocator("edX", "dot-underscore", "2014_Fall")
        content_store = Mock()
        content_store.generate_thumbnail.return_value = ("content", "location")
        static_content_importer = StaticContentImporter(
            static_content_store=content_store,
            course_data_path=course_dir,
            target_id=course_id
        )
        static_content_importer.import_static_content_directory()
        saved_static_content = [call[0][0] for call in content_store.save.call_args_list]
        name_val = {sc.name: sc.data for sc in saved_static_content}
        self.assertIn("example.txt", name_val)
        self.assertIn(".example.txt", name_val)
        self.assertNotIn("._example.txt", name_val)
        self.assertNotIn(".DS_Store", name_val)
        self.assertIn("GREEN", name_val["example.txt"])
        self.assertIn("BLUE", name_val[".example.txt"])
