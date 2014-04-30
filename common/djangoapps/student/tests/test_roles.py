"""
Tests of student.roles
"""

from django.test import TestCase

from xmodule.modulestore import Location
from courseware.tests.factories import UserFactory, StaffFactory, InstructorFactory
from student.tests.factories import AnonymousUserFactory

from student.roles import GlobalStaff, CourseRole, CourseStaffRole
from xmodule.modulestore.django import loc_mapper
from xmodule.modulestore.locator import BlockUsageLocator


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

    def test_course_role(self):
        """
        Test that giving a user a course role enables access appropriately
        """
        course_locator = loc_mapper().translate_location(
            self.course.course_id, self.course, add_entry_if_missing=True
        )
        self.assertFalse(
            CourseStaffRole(course_locator).has_user(self.student),
            "Student has premature access to {}".format(unicode(course_locator))
        )
        self.assertFalse(
            CourseStaffRole(self.course).has_user(self.student),
            "Student has premature access to {}".format(self.course.url())
        )
        CourseStaffRole(course_locator).add_users(self.student)
        self.assertTrue(
            CourseStaffRole(course_locator).has_user(self.student),
            "Student doesn't have access to {}".format(unicode(course_locator))
        )
        self.assertTrue(
            CourseStaffRole(self.course).has_user(self.student),
            "Student doesn't have access to {}".format(unicode(self.course.url()))
        )
        # now try accessing something internal to the course
        vertical_locator = BlockUsageLocator(
            package_id=course_locator.package_id, branch='published', block_id='madeup'
        )
        vertical_location = self.course.replace(category='vertical', name='madeuptoo')
        self.assertTrue(
            CourseStaffRole(vertical_locator).has_user(self.student),
            "Student doesn't have access to {}".format(unicode(vertical_locator))
        )
        self.assertTrue(
            CourseStaffRole(vertical_location, course_context=self.course.course_id).has_user(self.student),
            "Student doesn't have access to {}".format(unicode(vertical_location.url()))
        )

    def test_get_user_for_role(self):
        """
        test users_for_role
        """
        role = CourseStaffRole(self.course_id)
        role.add_users(self.student)
        self.assertGreater(len(role.users_with_role()), 0)

    def test_add_users_doesnt_add_duplicate_entry(self):
        """
        Tests that calling add_users multiple times before a single call
        to remove_users does not result in the user remaining in the group.
        """
        role = CourseStaffRole(self.course_id)
        role.add_users(self.student)
        self.assertTrue(role.has_user(self.student))
        # Call add_users a second time, then remove just once.
        role.add_users(self.student)
        role.remove_users(self.student)
        self.assertFalse(role.has_user(self.student))
