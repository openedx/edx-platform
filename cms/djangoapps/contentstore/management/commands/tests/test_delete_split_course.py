"""
Unittests for deleting a split mongo course
"""
import unittest

from django.core.management import CommandError, call_command
from django.test.utils import override_settings
from contentstore.management.commands.delete_split_course import Command
from contentstore.tests.modulestore_config import TEST_MODULESTORE
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.persistent_factories import PersistentCourseFactory
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
# pylint: disable=E1101


class TestArgParsing(unittest.TestCase):
    """
    Tests for parsing arguments for the `delete_split_course` management command
    """
    def setUp(self):
        self.command = Command()

    def test_no_args(self):
        errstring = "delete_split_course requires at least one argument"
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle()

    def test_invalid_locator(self):
        errstring = "Invalid locator string !?!"
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle("!?!")

    def test_nonexistant_locator(self):
        errstring = "No course found with locator course/branch/name"
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle("course/branch/name")


@override_settings(MODULESTORE=TEST_MODULESTORE)
class TestDeleteSplitCourse(ModuleStoreTestCase):
    """
    Unit tests for deleting a split-mongo course from command line
    """

    def setUp(self):
        super(TestDeleteSplitCourse, self).setUp()
        self.course = PersistentCourseFactory()

    def test_happy_path(self):
        locator = self.course.location
        call_command(
            "delete_split_course",
            str(locator),
        )
        with self.assertRaises(ItemNotFoundError):
            modulestore('split').get_course(locator)
