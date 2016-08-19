from opaque_keys.edx import locator
import unittest
import ddt

from django.contrib.auth.models import Group
from edx_solutions_api_integration.models import CourseGroupRelationship, GroupProfile
from student.management.commands import repair_internal_admin_instructor_role
from student.models import CourseEnrollment, CourseAccessRole
from student.tests.factories import UserFactory, GroupFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

@ddt.ddt
class TestRepairInternalAdminInstructorRole(ModuleStoreTestCase):
    """Tests for repair_internal_admin_instructor_role script."""

    PASSWORD = 'test'
    TEST_COURSES = 2
    TEST_USERS = 5

    def setUp(self, **kwargs):
        super(TestRepairInternalAdminInstructorRole, self).setUp()

        # Creating internal admin role
        self.internal_admin_group_name = 'mcka_role_internal_admin'
        self.internal_admin_group_type = 'permission'
        self.internal_admin_group = Group.objects.create(name=self.internal_admin_group_name)
        self.internal_admin_group.save()

        self.internal_admin_profile, self._ = GroupProfile.objects.get_or_create(group_id=self.internal_admin_group.id)
        self.internal_admin_profile.group_type = self.internal_admin_group_type
        self.internal_admin_profile.name = self.internal_admin_group_name
        self.internal_admin_profile.save()

        # Creating Internal Tag
        self.internal_tag_group_name = 'INTERNAL'
        self.internal_tag_group_type = 'tag:internal'
        self.internal_tag_group = Group.objects.create(name=self.internal_tag_group_name)
        self.internal_tag_group.save()

        self.internal_tag_profile, self._ = GroupProfile.objects.get_or_create(group_id=self.internal_tag_group.id)
        self.internal_tag_profile.group_type = self.internal_tag_group_type
        self.internal_tag_profile.name = self.internal_tag_group_name
        self.internal_tag_profile.save()

        # Creating courses
        self.course_list = []
        for index in range(0, self.TEST_COURSES):
            self.original_course_location = locator.CourseLocator('Org0'+str(index), 'Course0'+str(index), 'Run0'+str(index))
            self.course = self._create_course(self.original_course_location)
            self.course_list.append(self.course)

        # Creating users
        self.student_list = []

        for index in range(0, self.TEST_USERS):
            self.student = UserFactory.create()
            self.student.set_password(self.PASSWORD)  # pylint: disable=no-member
            self.student.save()   # pylint: disable=no-member

            # Adding user to internal admin group
            self.internal_admin_group.user_set.add(self.student.id)

            self.student_list.append(self.student)

    def test_removing_instructor_role_from_courses(self):

        # Add instructor role
        for student in self.student_list:
            for course in self.course_list:
                new_role = CourseAccessRole.objects.create(user=student, role='instructor', course_id=course.id)
                new_role.save()

        # Run the actual management command
        repair_internal_admin_instructor_role.Command().handle('repair')

        # Check if instructor role is deleted (user does not have nay more roles)
        for student in self.student_list:
            for course in self.course_list:
                roles = CourseAccessRole.objects.filter(user=student, course_id=course.id)
                self.assertEquals(len(roles), 0)


    def test_adding_instructor_role_to_courses(self):

        # Adding internal tag to a course
        for course in self.course_list:
            CourseGroupRelationship.objects.create(course_id=course.id, group=self.internal_tag_group)

        # Run the actual management command
        repair_internal_admin_instructor_role.Command().handle('repair')

        # Check if instructor role is added
        for student in self.student_list:
            for course in self.course_list:
                roles = CourseAccessRole.objects.filter(user=student, course_id=course.id)
                for role_data in roles:
                    self.assertEquals('instructor', role_data.role)

    def test_removing_instructor_role_if_user_is_also_staff(self):

        # Add instructor and staff role
        for student in self.student_list:
            for course in self.course_list:
                new_role = CourseAccessRole.objects.create(user=student, role='instructor', course_id=course.id)
                new_role.save()
                new_role = CourseAccessRole.objects.create(user=student, role='staff', course_id=course.id)
                new_role.save()

        # Run the actual management command
        repair_internal_admin_instructor_role.Command().handle('repair')

        # Check if user still has 2 roles
        for student in self.student_list:
            for course in self.course_list:
                roles = CourseAccessRole.objects.filter(user=student, course_id=course.id)
                self.assertEquals(len(roles), 2)

    def test_removing_instructor_role_from_internal_course(self):

        # Add internal Tag to all courses
        for course in self.course_list:
            CourseGroupRelationship.objects.create(course_id=course.id, group=self.internal_tag_group)

        # Add instructor role
        for student in self.student_list:
            for course in self.course_list:
                new_role = CourseAccessRole.objects.create(user=student, role='instructor', course_id=course.id)
                new_role.save()

        # Run the actual management command
        repair_internal_admin_instructor_role.Command().handle('repair', 'createlog')

        # Check if instructor role is not deleted
        for student in self.student_list:
            for course in self.course_list:
                roles = CourseAccessRole.objects.filter(user=student, course_id=course.id)
                for role_data in roles:
                    self.assertEquals('instructor', role_data.role)


    def _create_course(self, course_location):
        """ Creates a course """
        return CourseFactory.create(
            org=course_location.org,
            number=course_location.course,
            run=course_location.run
        )
