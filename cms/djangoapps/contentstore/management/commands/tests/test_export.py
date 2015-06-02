import unittest
import ddt
from django.core.management import CommandError
from tempfile import mkdtemp

from xmodule.modulestore.tests.factories import CourseFactory
from contentstore.management.commands.export import Command
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.django import modulestore


class TestArgParsingCourseExport(unittest.TestCase):
    """
    Tests for parsing arguments for the `export` management command
    """
    def setUp(self):
        super(TestArgParsingCourseExport, self).setUp()

        self.command = Command()

    def test_no_args(self):
        errstring = "export requires two arguments: <course id> <output path>"
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle()


@ddt.ddt
class TestCourseExport(ModuleStoreTestCase):
    """
    Test exporting a course
    """
    def setUp(self):
        super(TestCourseExport, self).setUp()

        # Make directory at the current location
        self.temp_dir = mkdtemp(dir="")

        self.command = Command()

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
        with self.assertRaises(Exception):
            self.command.handle("InvalidCourseID", self.temp_dir)

        # Test `export` management command with correct course_id
        self.command.handle(course_id, self.temp_dir)
