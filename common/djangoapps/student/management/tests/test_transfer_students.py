"""
Tests the transfer student management command
"""
from django.conf import settings
from opaque_keys.edx import locator
import unittest
import ddt
from student.management.commands import transfer_students
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
@ddt.ddt
class TestTransferStudents(ModuleStoreTestCase):
    """Tests for transferring students between courses."""

    PASSWORD = 'test'

    def test_transfer_students(self):
        student = UserFactory()
        student.set_password(self.PASSWORD)  # pylint: disable=E1101
        student.save()   # pylint: disable=E1101

        # Original Course
        original_course_location = locator.CourseLocator('Org0', 'Course0', 'Run0')
        course = self._create_course(original_course_location)
        # Enroll the student in 'verified'
        CourseEnrollment.enroll(student, course.id, mode="verified")

        # New Course 1
        course_location_one = locator.CourseLocator('Org1', 'Course1', 'Run1')
        new_course_one = self._create_course(course_location_one)

        # New Course 2
        course_location_two = locator.CourseLocator('Org2', 'Course2', 'Run2')
        new_course_two = self._create_course(course_location_two)
        original_key = unicode(course.id)
        new_key_one = unicode(new_course_one.id)
        new_key_two = unicode(new_course_two.id)

        # Run the actual management command
        transfer_students.Command().handle(
            source_course=original_key, dest_course_list=new_key_one + "," + new_key_two
        )

        # Confirm the enrollment mode is verified on the new courses, and enrollment is enabled as appropriate.
        self.assertEquals(('verified', False), CourseEnrollment.enrollment_mode_for_user(student, course.id))
        self.assertEquals(('verified', True), CourseEnrollment.enrollment_mode_for_user(student, new_course_one.id))
        self.assertEquals(('verified', True), CourseEnrollment.enrollment_mode_for_user(student, new_course_two.id))

    def _create_course(self, course_location):
        """ Creates a course """
        return CourseFactory.create(
            org=course_location.org,
            number=course_location.course,
            run=course_location.run
        )
