"""
Tests that check that we ignore the appropriate files when importing courses.
"""
import unittest
from mock import Mock
from xmodule.modulestore.xml_importer import import_static_content
from xmodule.modulestore.locations import SlashSeparatedCourseKey
from xmodule.tests import DATA_DIR


class IgnoredFilesTestCase(unittest.TestCase):
    "Tests for ignored files"
    def test_ignore_tilde_static_files(self):
        course_dir = DATA_DIR / "tilde"
        course_id = SlashSeparatedCourseKey("edX", "tilde", "Fall_2012")
        content_store = Mock()
        content_store.generate_thumbnail.return_value = ("content", "location")
        import_static_content(course_dir, content_store, course_id)
        saved_static_content = [call[0][0] for call in content_store.save.call_args_list]
        name_val = {sc.name: sc.data for sc in saved_static_content}
        self.assertIn("example.txt", name_val)
        self.assertNotIn("example.txt~", name_val)
        self.assertIn("GREEN", name_val["example.txt"])
