"""
Tests of student.roles
"""
import ddt
from django.test import TestCase

from courseware.tests.factories import UserFactory, StaffFactory, InstructorFactory
from student.tests.factories import AnonymousUserFactory

from student.roles import (
    GlobalStaff, CourseRole, CourseStaffRole, CourseInstructorRole,
    OrgStaffRole, OrgInstructorRole, RoleCache, CourseBetaTesterRole
)
from opaque_keys.edx.locations import SlashSeparatedCourseKey


class RolesTestCase(TestCase):
    """
    Tests of student.roles
    """

    def setUp(self):
        super(RolesTestCase, self).setUp()
        self.course_key = SlashSeparatedCourseKey('edX', 'toy', '2012_Fall')
        self.course_loc = self.course_key.make_usage_key('course', '2012_Fall')
        self.anonymous_user = AnonymousUserFactory()
        self.student = UserFactory()
        self.global_staff = UserFactory(is_staff=True)
        self.course_staff = StaffFactory(course_key=self.course_key)
        self.course_instructor = InstructorFactory(course_key=self.course_key)

    def test_global_staff(self):
        self.assertFalse(GlobalStaff().has_user(self.student))
        self.assertFalse(GlobalStaff().has_user(self.course_staff))
        self.assertFalse(GlobalStaff().has_user(self.course_instructor))
        self.assertTrue(GlobalStaff().has_user(self.global_staff))

    def test_group_name_case_sensitive(self):
        uppercase_course_id = "ORG/COURSE/NAME"
        lowercase_course_id = uppercase_course_id.lower()
        uppercase_course_key = SlashSeparatedCourseKey.from_deprecated_string(uppercase_course_id)
        lowercase_course_key = SlashSeparatedCourseKey.from_deprecated_string(lowercase_course_id)

        role = "role"

        lowercase_user = UserFactory()
        CourseRole(role, lowercase_course_key).add_users(lowercase_user)
        uppercase_user = UserFactory()
        CourseRole(role, uppercase_course_key).add_users(uppercase_user)

        self.assertTrue(CourseRole(role, lowercase_course_key).has_user(lowercase_user))
        self.assertFalse(CourseRole(role, uppercase_course_key).has_user(lowercase_user))
        self.assertFalse(CourseRole(role, lowercase_course_key).has_user(uppercase_user))
        self.assertTrue(CourseRole(role, uppercase_course_key).has_user(uppercase_user))

    def test_course_role(self):
        """
        Test that giving a user a course role enables access appropriately
        """
        self.assertFalse(
            CourseStaffRole(self.course_key).has_user(self.student),
            "Student has premature access to {}".format(self.course_key)
        )
        CourseStaffRole(self.course_key).add_users(self.student)
        self.assertTrue(
            CourseStaffRole(self.course_key).has_user(self.student),
            "Student doesn't have access to {}".format(unicode(self.course_key))
        )

        # remove access and confirm
        CourseStaffRole(self.course_key).remove_users(self.student)
        self.assertFalse(
            CourseStaffRole(self.course_key).has_user(self.student),
            "Student still has access to {}".format(self.course_key)
        )

    def test_org_role(self):
        """
        Test that giving a user an org role enables access appropriately
        """
        self.assertFalse(
            OrgStaffRole(self.course_key.org).has_user(self.student),
            "Student has premature access to {}".format(self.course_key.org)
        )
        OrgStaffRole(self.course_key.org).add_users(self.student)
        self.assertTrue(
            OrgStaffRole(self.course_key.org).has_user(self.student),
            "Student doesn't have access to {}".format(unicode(self.course_key.org))
        )

        # remove access and confirm
        OrgStaffRole(self.course_key.org).remove_users(self.student)
        if hasattr(self.student, '_roles'):
            del self.student._roles
        self.assertFalse(
            OrgStaffRole(self.course_key.org).has_user(self.student),
            "Student still has access to {}".format(self.course_key.org)
        )

    def test_org_and_course_roles(self):
        """
        Test that Org and course roles don't interfere with course roles or vice versa
        """
        OrgInstructorRole(self.course_key.org).add_users(self.student)
        CourseInstructorRole(self.course_key).add_users(self.student)
        self.assertTrue(
            OrgInstructorRole(self.course_key.org).has_user(self.student),
            "Student doesn't have access to {}".format(unicode(self.course_key.org))
        )
        self.assertTrue(
            CourseInstructorRole(self.course_key).has_user(self.student),
            "Student doesn't have access to {}".format(unicode(self.course_key))
        )

        # remove access and confirm
        OrgInstructorRole(self.course_key.org).remove_users(self.student)
        self.assertFalse(
            OrgInstructorRole(self.course_key.org).has_user(self.student),
            "Student still has access to {}".format(self.course_key.org)
        )
        self.assertTrue(
            CourseInstructorRole(self.course_key).has_user(self.student),
            "Student doesn't have access to {}".format(unicode(self.course_key))
        )

        # ok now keep org role and get rid of course one
        OrgInstructorRole(self.course_key.org).add_users(self.student)
        CourseInstructorRole(self.course_key).remove_users(self.student)
        self.assertTrue(
            OrgInstructorRole(self.course_key.org).has_user(self.student),
            "Student lost has access to {}".format(self.course_key.org)
        )
        self.assertFalse(
            CourseInstructorRole(self.course_key).has_user(self.student),
            "Student doesn't have access to {}".format(unicode(self.course_key))
        )

    def test_get_user_for_role(self):
        """
        test users_for_role
        """
        role = CourseStaffRole(self.course_key)
        role.add_users(self.student)
        self.assertGreater(len(role.users_with_role()), 0)

    def test_add_users_doesnt_add_duplicate_entry(self):
        """
        Tests that calling add_users multiple times before a single call
        to remove_users does not result in the user remaining in the group.
        """
        role = CourseStaffRole(self.course_key)
        role.add_users(self.student)
        self.assertTrue(role.has_user(self.student))
        # Call add_users a second time, then remove just once.
        role.add_users(self.student)
        role.remove_users(self.student)
        self.assertFalse(role.has_user(self.student))


@ddt.ddt
class RoleCacheTestCase(TestCase):

    IN_KEY = SlashSeparatedCourseKey('edX', 'toy', '2012_Fall')
    NOT_IN_KEY = SlashSeparatedCourseKey('edX', 'toy', '2013_Fall')

    ROLES = (
        (CourseStaffRole(IN_KEY), ('staff', IN_KEY, 'edX')),
        (CourseInstructorRole(IN_KEY), ('instructor', IN_KEY, 'edX')),
        (OrgStaffRole(IN_KEY.org), ('staff', None, 'edX')),
        (OrgInstructorRole(IN_KEY.org), ('instructor', None, 'edX')),
        (CourseBetaTesterRole(IN_KEY), ('beta_testers', IN_KEY, 'edX')),
    )

    def setUp(self):
        super(RoleCacheTestCase, self).setUp()
        self.user = UserFactory()

    @ddt.data(*ROLES)
    @ddt.unpack
    def test_only_in_role(self, role, target):
        role.add_users(self.user)
        cache = RoleCache(self.user)
        self.assertTrue(cache.has_role(*target))

        for other_role, other_target in self.ROLES:
            if other_role == role:
                continue

            self.assertFalse(cache.has_role(*other_target))

    @ddt.data(*ROLES)
    @ddt.unpack
    def test_empty_cache(self, role, target):
        cache = RoleCache(self.user)
        self.assertFalse(cache.has_role(*target))
