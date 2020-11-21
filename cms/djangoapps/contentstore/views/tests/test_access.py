"""
Tests access.py
"""


from django.contrib.auth.models import User
from django.test import TestCase
from opaque_keys.edx.locator import CourseLocator

from common.djangoapps.student.auth import add_users
from common.djangoapps.student.roles import CourseInstructorRole, CourseStaffRole
from common.djangoapps.student.tests.factories import AdminFactory

from ..access import get_user_role


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
