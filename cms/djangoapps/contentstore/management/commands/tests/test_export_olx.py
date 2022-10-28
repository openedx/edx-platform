"""
Tests for exporting OLX content.
"""


import shutil
import tarfile
import unittest
from io import StringIO
from tempfile import mkdtemp

from django.core.management import CommandError, call_command
from path import Path as path

from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class TestArgParsingCourseExportOlx(unittest.TestCase):
    """
    Tests for parsing arguments for the `export_olx` management command
    """
    def test_no_args(self):
        """
        Test export command with no arguments
        """
        errstring = "Error: the following arguments are required: course_id"
        with self.assertRaisesRegex(CommandError, errstring):
            call_command('export_olx')


class TestCourseExportOlx(ModuleStoreTestCase):
    """
    Test exporting OLX content from a course or library.
    """

    def test_invalid_course_key(self):
        """
        Test export command with an invalid course key.
        """
        errstring = "Unparsable course_id"
        with self.assertRaisesRegex(CommandError, errstring):
            call_command('export_olx', 'InvalidCourseID')

    def test_course_key_not_found(self):
        """
        Test export command with a valid course key that doesn't exist.
        """
        errstring = "Invalid course_id"
        with self.assertRaisesRegex(CommandError, errstring):
            call_command('export_olx', 'x/y/z')

    def create_dummy_course(self, store_type):
        """Create small course."""
        course = CourseFactory.create(default_store=store_type)
        self.assertTrue(
            modulestore().has_course(course.id),
            f"Could not find course in {store_type}"
        )
        return course.id

    def check_export_file(self, tar_file, course_key):
        """Check content of export file."""
        names = tar_file.getnames()
        dirname = "{0.org}-{0.course}-{0.run}".format(course_key)
        self.assertIn(dirname, names)
        # Check if some of the files are present, without being exhaustive.
        self.assertIn(f"{dirname}/about", names)
        self.assertIn(f"{dirname}/about/overview.html", names)
        self.assertIn(f"{dirname}/assets/assets.xml", names)
        self.assertIn(f"{dirname}/policies", names)

    def test_export_course(self):
        test_course_key = self.create_dummy_course(ModuleStoreEnum.Type.split)
        tmp_dir = path(mkdtemp())
        self.addCleanup(shutil.rmtree, tmp_dir)
        filename = tmp_dir / 'test.tar.gz'
        call_command('export_olx', '--output', filename, str(test_course_key))
        with tarfile.open(filename) as tar_file:
            self.check_export_file(tar_file, test_course_key)

    # There is a bug in the underlying management/base code that tries to make
    # all manageent command output be unicode.  This management command
    # outputs the binary tar file data and so breaks in python3.  In python2
    # the code is happy to pass bytes back and forth and in later versions of
    # django this is fixed.  Howevere it's not possible to get this test to
    # pass in Python3 and django 1.11
    @unittest.skip("Bug in django 1.11 prevents this from working in python3.  Re-enable after django 2.x upgrade.")
    def test_export_course_stdout(self):
        test_course_key = self.create_dummy_course(ModuleStoreEnum.Type.split)
        out = StringIO()
        call_command('export_olx', str(test_course_key), stdout=out)
        out.seek(0)
        output = out.read()
        with tarfile.open(fileobj=StringIO(output)) as tar_file:
            self.check_export_file(tar_file, test_course_key)
