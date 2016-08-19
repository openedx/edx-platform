"""
Tests the transfer student management command
"""
from opaque_keys.edx import locator
import unittest
import ddt

from student.management.commands import repair_users_roles_on_all_courses
from student.models import CourseEnrollment, CourseAccessRole
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

@ddt.ddt
class TestRepairUsersRolesOnAllCourses(ModuleStoreTestCase):
    """Tests for transferring students between courses."""

    PASSWORD = "test"
    TEST_USERS = 10
    TEST_COURSES = 10
    def setUp(self, **kwargs):
        super(TestRepairUsersRolesOnAllCourses, self).setUp()

    def test_user_repair(self):
        """ Verify the role cleanup script"""
        
        username_list = []
        student_list = []
        course_list = []
        for index in range(0, self.TEST_COURSES):
            original_course_location = locator.CourseLocator('Org0'+str(index), 'Course0'+str(index), 'Run0'+str(index))
            course = self._create_course(original_course_location)
            course_list.append(course)

        for index in range(0, self.TEST_USERS):
            username_list.append("test_repair_user_"+str(index))
            student = UserFactory.create()
            student.set_password(self.PASSWORD)  # pylint: disable=no-member
            student.save()   # pylint: disable=no-member

            # Enroll the student in 'verified' and add both observer and assistant
            for course in course_list:
                CourseEnrollment.enroll(student, course.id, mode="verified")
                CourseAccessRole.objects.create(user=student, role="observer", course_id=course.id)
                CourseAccessRole.objects.create(user=student, role="assistant", course_id=course.id)

            student_list.append(student)


        # Run the actual management command
        repair_users_roles_on_all_courses.Command().handle("repair", "createlog")

        for index in range(0, self.TEST_USERS):
            for course in course_list:
                roles = CourseAccessRole.objects.filter(user=student_list[index], course_id=course.id)
                for role_data in roles:
                    self.assertEquals("assistant", role_data.role)

    def _create_course(self, course_location):
        """ Creates a course """
        return CourseFactory.create(
            org=course_location.org,
            number=course_location.course,
            run=course_location.run
        )

