"""
Tests for exporting courseware to the desired path
"""
import unittest
import shutil
import ddt
from django.core.management import CommandError, call_command
from tempfile import mkdtemp

from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.django import modulestore


class TestArgParsingCourseExport(unittest.TestCase):
    """
    Tests for parsing arguments for the `export` management command
    """
    def setUp(self):
        super(TestArgParsingCourseExport, self).setUp()

    def test_no_args(self):
        """
        Test export command with no arguments
        """
        errstring = "export requires two arguments: <course id> <output path>"
        with self.assertRaises(SystemExit) as ex:
            with self.assertRaisesRegexp(CommandError, errstring):
                call_command('export')
        self.assertEqual(ex.exception.code, 1)


@ddt.ddt
class TestCourseExport(ModuleStoreTestCase):
    """
    Test exporting a course
    """
    def setUp(self):
        super(TestCourseExport, self).setUp()

        # Temp directories (temp_dir_1: relative path, temp_dir_2: absolute path)
        self.temp_dir_1 = mkdtemp()
        self.temp_dir_2 = mkdtemp(dir="")

        # Clean temp directories
        self.addCleanup(shutil.rmtree, self.temp_dir_1)
        self.addCleanup(shutil.rmtree, self.temp_dir_2)

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_export_course_with_directory_name(self, store):
        """
        Create a new course try exporting in a path specified
        """
        course = CourseFactory.create(default_store=store)
        course_id = unicode(course.id)
        self.assertTrue(
            modulestore().has_course(course.id),
            "Could not find course in {}".format(store)
        )
        # Test `export` management command with invalid course_id
        errstring = "Invalid course_key 'InvalidCourseID'."
        with self.assertRaises(SystemExit) as ex:
            with self.assertRaisesRegexp(CommandError, errstring):
                call_command('export', "InvalidCourseID", self.temp_dir_1)
        self.assertEqual(ex.exception.code, 1)

        # Test `export` management command with correct course_id
        for output_dir in [self.temp_dir_1, self.temp_dir_2]:
            call_command('export', course_id, output_dir)

    def test_course_key_not_found(self):
        """
        Test export command with a valid course key that doesn't exist
        """
        errstring = "Course with x/y/z key not found."
        with self.assertRaises(SystemExit) as ex:
            with self.assertRaisesRegexp(CommandError, errstring):
                call_command('export', "x/y/z", self.temp_dir_1)
        self.assertEqual(ex.exception.code, 1)
