"""
Tests of student.roles
"""

from django.test import TestCase

from xmodule.modulestore import Location
from courseware.tests.factories import UserFactory, StaffFactory, InstructorFactory
from student.tests.factories import AnonymousUserFactory

from student.roles import GlobalStaff, CourseRole


class RolesTestCase(TestCase):
    """
    Tests of student.roles
    """

    def setUp(self):
        self.course = Location('i4x://edX/toy/course/2012_Fall')
        self.anonymous_user = AnonymousUserFactory()
        self.student = UserFactory()
        self.global_staff = UserFactory(is_staff=True)
        self.course_staff = StaffFactory(course=self.course)
        self.course_instructor = InstructorFactory(course=self.course)

    def test_global_staff(self):
        self.assertFalse(GlobalStaff().has_user(self.student))
        self.assertFalse(GlobalStaff().has_user(self.course_staff))
        self.assertFalse(GlobalStaff().has_user(self.course_instructor))
        self.assertTrue(GlobalStaff().has_user(self.global_staff))

    def test_group_name_case_insensitive(self):
        uppercase_loc = "i4x://ORG/COURSE/course/NAME"
        lowercase_loc = uppercase_loc.lower()

        lowercase_group = "role_org/course/name"
        uppercase_group = lowercase_group.upper()

        lowercase_user = UserFactory(groups=lowercase_group)
        uppercase_user = UserFactory(groups=uppercase_group)

        self.assertTrue(CourseRole("role", lowercase_loc).has_user(lowercase_user))
        self.assertTrue(CourseRole("role", uppercase_loc).has_user(lowercase_user))
        self.assertTrue(CourseRole("role", lowercase_loc).has_user(uppercase_user))
        self.assertTrue(CourseRole("role", uppercase_loc).has_user(uppercase_user))

