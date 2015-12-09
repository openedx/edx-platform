"""
Unittests for deleting a course in an chosen modulestore
"""

import unittest
import mock

from opaque_keys.edx.locations import SlashSeparatedCourseKey
from django.core.management import call_command, CommandError
from contentstore.tests.utils import CourseTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.django import modulestore


class DeleteCourseTest(CourseTestCase):
    """
    Test for course deleting functionality of the 'delete_course' command
    """

    YESNO_PATCH_LOCATION = 'contentstore.management.commands.delete_course.query_yes_no'

    def setUp(self):
        super(DeleteCourseTest, self).setUp()

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
        errstring = "Invalid course_key: 'TestX/TS01/2015_Q7'. Proper syntax: 'org/number/run' "
        with self.assertRaisesRegexp(CommandError, errstring):
            call_command('delete_course','TestX/TS01/2015_Q7')

    def test_course_deleted(self):
        """
        Testing if the entered course was deleted
        """

        #Test if the course that is about to be deleted exists
        self.assertIsNotNone(modulestore().get_course(SlashSeparatedCourseKey("TestX", "TS01", "2015_Q1")))

        with mock.patch(self.YESNO_PATCH_LOCATION) as patched_yes_no:
            patched_yes_no.return_value = True
            call_command('delete_course','TestX/TS01/2015_Q1', "commit")
            self.assertIsNone(modulestore().get_course(SlashSeparatedCourseKey("TestX", "TS01", "2015_Q1")))
