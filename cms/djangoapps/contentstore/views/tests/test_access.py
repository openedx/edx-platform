"""
Tests access.py
"""
from django.contrib.auth.models import User
from django.test import TestCase
from opaque_keys.edx.locator import CourseLocator

from contentstore.views.access import get_user_role
from student.auth import add_users
from student.roles import (
    CourseCreatorRole,
    CourseInstructorRole,
    CourseStaffRole,
    GlobalCourseCreatorRole,
    GlobalStaff,
)
from student.tests.factories import AdminFactory


class RolesTest(TestCase):
    """
    Tests for lti user role serialization.
    """
    def setUp(self):
        """ Test case setup """
        super(RolesTest, self).setUp()

        self.global_admin = AdminFactory()
        self.instructor = User.objects.create_user('testinstructor', 'testinstructor+courses@edx.org', 'foo')
        self.staff = User.objects.create_user('teststaff', 'teststaff+courses@edx.org', 'foo')
        self.course_creator = User.objects.create_user('testcoursecreator', 'testcoursecreator+courses@edx.org', 'foo')
        self.global_course_creator = User.objects.create_user(
            'testglobalcoursecreator', 'testglobalcoursecreator+courses@edx.org', 'foo'
            )
        self.course_key = CourseLocator('mitX', '101', 'test')

    def test_get_user_role_instructor(self):
        """
        Verifies if user is instructor.
        """
        add_users(self.global_admin, CourseInstructorRole(self.course_key), self.instructor)
        self.assertEqual(
            'instructor',
            get_user_role(self.instructor, self.course_key)
        )
        add_users(self.global_admin, CourseStaffRole(self.course_key), self.staff)
        self.assertEqual(
            'instructor',
            get_user_role(self.instructor, self.course_key)
        )

    def test_get_user_role_staff(self):
        """
        Verifies if user is staff.
        """
        add_users(self.global_admin, CourseStaffRole(self.course_key), self.staff)
        self.assertEqual(
            'staff',
            get_user_role(self.staff, self.course_key)
        )

    def test_enrollment_end_editable(self):
        """
        Verifies if user can edit enrollment end date.
        """
        add_users(self.global_admin, CourseCreatorRole(), self.course_creator)
        assert GlobalStaff().has_user(
                self.course_creator
            ) or CourseCreatorRole().has_user(
                self.course_creator
            ) or not marketing_site_enabled
        add_users(self.global_admin, GlobalCourseCreatorRole(), self.global_course_creator)
        assert GlobalStaff().has_user(
                self.global_course_creator
            ) or GlobalCourseCreatorRole().has_user(
                self.global_course_creator
            ) or not marketing_site_enabled
