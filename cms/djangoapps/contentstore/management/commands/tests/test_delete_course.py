"""
Unittests for deleting a course in an chosen modulestore
"""

import mock

from opaque_keys.edx.locations import SlashSeparatedCourseKey
from django.core.management import call_command, CommandError
from django.contrib.auth.models import User
from contentstore.tests.utils import CourseTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.django import modulestore
from student.roles import CourseInstructorRole


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

    def test_invalid_key_not_found(self):
        """
        Test for when a course key is malformed
        """
        errstring = "Invalid course_key: 'foo/TestX/TS01/2015_Q7'."
        with self.assertRaisesRegexp(CommandError, errstring):
            call_command('delete_course', 'foo/TestX/TS01/2015_Q7')

    def test_course_key_not_found(self):
        """
        Test for when a non-existing course key is entered
        """
        errstring = "Course with 'TestX/TS01/2015_Q7' key not found."
        with self.assertRaisesRegexp(CommandError, errstring):
            call_command('delete_course', 'TestX/TS01/2015_Q7')

    def test_course_deleted(self):
        """
        Testing if the entered course was deleted
        """

        #Test if the course that is about to be deleted exists
        self.assertIsNotNone(modulestore().get_course(SlashSeparatedCourseKey("TestX", "TS01", "2015_Q1")))

        with mock.patch(self.YESNO_PATCH_LOCATION) as patched_yes_no:
            patched_yes_no.return_value = True
            call_command('delete_course', 'TestX/TS01/2015_Q1')
            self.assertIsNone(modulestore().get_course(SlashSeparatedCourseKey("TestX", "TS01", "2015_Q1")))

    def test_course_deletion_with_keep_instructors(self):
        """
        Tests that deleting course with keep-instructors option do not remove instructors from course.
        """
        instructor_user = User.objects.create(
            username='test_instructor',
            email='test_email@example.com'
        )
        self.assertIsNotNone(instructor_user)

        # Add and verify instructor role for the course
        instructor_role = CourseInstructorRole(self.course.id)
        instructor_role.add_users(instructor_user)
        self.assertTrue(instructor_role.has_user(instructor_user))

        # Verify the course we are about to delete exists in the modulestore
        self.assertIsNotNone(modulestore().get_course(self.course.id))

        with mock.patch(self.YESNO_PATCH_LOCATION, return_value=True):
            call_command('delete_course', 'TestX/TS01/2015_Q1', '--keep-instructors')

        self.assertIsNone(modulestore().get_course(self.course.id))
        self.assertTrue(instructor_role.has_user(instructor_user))
