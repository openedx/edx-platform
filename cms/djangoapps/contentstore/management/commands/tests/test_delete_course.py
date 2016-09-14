"""
Unittests for deleting a course in an chosen modulestore
"""

import unittest
import mock

from opaque_keys.edx.locations import SlashSeparatedCourseKey
from django.core.management import CommandError
from contentstore.management.commands.delete_course import Command
from contentstore.tests.utils import CourseTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.django import modulestore


class TestArgParsing(unittest.TestCase):
    """
    Tests for parsing arguments for the 'delete_course'  management command
    """

    def setUp(self):
        super(TestArgParsing, self).setUp()

        self.command = Command()

    def test_no_args(self):
        """
        Testing 'delete_course' command with no arguments provided
        """
        errstring = "Arguments missing: 'org/number/run commit'"
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle()

    def test_no_course_key(self):
        """
        Testing 'delete_course' command with no course key provided
        """
        errstring = "Delete_course requires a course_key <org/number/run> argument."
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle("commit")

    def test_commit_argument(self):
        """
        Testing 'delete_course' command without 'commit' argument
        """
        errstring = "Delete_course requires a commit argument at the end"
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle("TestX/TS01/run")

    def test_invalid_course_key(self):
        """
        Testing 'delete_course' command with an invalid course key argument
        """
        errstring = "Invalid course_key: 'TestX/TS01'. Proper syntax: 'org/number/run commit' "
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle("TestX/TS01", "commit")

    def test_missing_commit_argument(self):
        """
        Testing 'delete_course' command with misspelled 'commit' argument
        """
        errstring = "Delete_course requires a commit argument at the end"
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle("TestX/TS01/run", "comit")

    def test_too_many_arguments(self):
        """
        Testing 'delete_course' command with more than 2 arguments
        """
        errstring = "Too many arguments! Expected <course_key> <commit>"
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle("TestX/TS01/run", "commit", "invalid")


class DeleteCourseTest(CourseTestCase):
    """
    Test for course deleting functionality of the 'delete_course' command
    """

    YESNO_PATCH_LOCATION = 'contentstore.management.commands.delete_course.query_yes_no'

    def setUp(self):
        super(DeleteCourseTest, self).setUp()

        self.command = Command()

        org = 'TestX'
        course_number = 'TS01'
        course_run = '2015_Q1'

        # Create a course using split modulestore
        self.course = CourseFactory.create(
            org=org,
            number=course_number,
            run=course_run
        )

    def test_course_key_not_found(self):
        """
        Test for when a non-existing course key is entered
        """
        errstring = "Course with 'TestX/TS01/2015_Q7' key not found."
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle('TestX/TS01/2015_Q7', "commit")

    def test_course_deleted(self):
        """
        Testing if the entered course was deleted
        """

        #Test if the course that is about to be deleted exists
        self.assertIsNotNone(modulestore().get_course(SlashSeparatedCourseKey("TestX", "TS01", "2015_Q1")))

        with mock.patch(self.YESNO_PATCH_LOCATION) as patched_yes_no:
            patched_yes_no.return_value = True
            self.command.handle('TestX/TS01/2015_Q1', "commit")
            self.assertIsNone(modulestore().get_course(SlashSeparatedCourseKey("TestX", "TS01", "2015_Q1")))
