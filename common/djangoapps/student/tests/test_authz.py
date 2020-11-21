"""
Tests authz.py
"""


import mock
from ccx_keys.locator import CCXLocator
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from opaque_keys.edx.locator import CourseLocator

from common.djangoapps.student.auth import add_users, has_studio_read_access, has_studio_write_access, remove_users, user_has_role
from common.djangoapps.student.roles import CourseCreatorRole, CourseInstructorRole, CourseStaffRole
from common.djangoapps.student.tests.factories import AdminFactory


class CreatorGroupTest(TestCase):
    """
    Tests for the course creator group.
    """

    def setUp(self):
        """ Test case setup """
        super(CreatorGroupTest, self).setUp()
        self.user = User.objects.create_user('testuser', 'test+courses@edx.org', 'foo')
        self.admin = User.objects.create_user('Mark', 'admin+courses@edx.org', 'foo')
        self.admin.is_staff = True

    def test_creator_group_not_enabled(self):
        """
        Tests that CourseCreatorRole().has_user always returns True if ENABLE_CREATOR_GROUP
        and DISABLE_COURSE_CREATION are both not turned on.
        """
        self.assertTrue(user_has_role(self.user, CourseCreatorRole()))

    def test_creator_group_enabled_but_empty(self):
        """ Tests creator group feature on, but group empty. """
        with mock.patch.dict('django.conf.settings.FEATURES', {"ENABLE_CREATOR_GROUP": True}):
            self.assertFalse(user_has_role(self.user, CourseCreatorRole()))

            # Make user staff. This will cause CourseCreatorRole().has_user to return True.
            self.user.is_staff = True
            self.assertTrue(user_has_role(self.user, CourseCreatorRole()))

    def test_creator_group_enabled_nonempty(self):
        """ Tests creator group feature on, user added. """
        with mock.patch.dict('django.conf.settings.FEATURES', {"ENABLE_CREATOR_GROUP": True}):
            add_users(self.admin, CourseCreatorRole(), self.user)
            self.assertTrue(user_has_role(self.user, CourseCreatorRole()))

            # check that a user who has not been added to the group still returns false
            user_not_added = User.objects.create_user('testuser2', 'test+courses2@edx.org', 'foo2')
            self.assertFalse(user_has_role(user_not_added, CourseCreatorRole()))

            # remove first user from the group and verify that CourseCreatorRole().has_user now returns false
            remove_users(self.admin, CourseCreatorRole(), self.user)
            self.assertFalse(user_has_role(self.user, CourseCreatorRole()))

    def test_course_creation_disabled(self):
        """ Tests that the COURSE_CREATION_DISABLED flag overrides course creator group settings. """
        with mock.patch.dict('django.conf.settings.FEATURES',
                             {'DISABLE_COURSE_CREATION': True, "ENABLE_CREATOR_GROUP": True}):
            # Add user to creator group.
            add_users(self.admin, CourseCreatorRole(), self.user)

            # DISABLE_COURSE_CREATION overrides (user is not marked as staff).
            self.assertFalse(user_has_role(self.user, CourseCreatorRole()))

            # Mark as staff. Now CourseCreatorRole().has_user returns true.
            self.user.is_staff = True
            self.assertTrue(user_has_role(self.user, CourseCreatorRole()))

            # Remove user from creator group. CourseCreatorRole().has_user still returns true because is_staff=True
            remove_users(self.admin, CourseCreatorRole(), self.user)
            self.assertTrue(user_has_role(self.user, CourseCreatorRole()))

    def test_add_user_not_authenticated(self):
        """
        Tests that adding to creator group fails if user is not authenticated
        """
        with mock.patch.dict(
            'django.conf.settings.FEATURES',
            {'DISABLE_COURSE_CREATION': False, "ENABLE_CREATOR_GROUP": True}
        ):
            anonymous_user = AnonymousUser()
            role = CourseCreatorRole()
            add_users(self.admin, role, anonymous_user)
            self.assertFalse(user_has_role(anonymous_user, role))

    def test_add_user_not_active(self):
        """
        Tests that adding to creator group fails if user is not active
        """
        with mock.patch.dict(
            'django.conf.settings.FEATURES',
            {'DISABLE_COURSE_CREATION': False, "ENABLE_CREATOR_GROUP": True}
        ):
            self.user.is_active = False
            add_users(self.admin, CourseCreatorRole(), self.user)
            self.assertFalse(user_has_role(self.user, CourseCreatorRole()))

    def test_add_user_to_group_requires_staff_access(self):
        with self.assertRaises(PermissionDenied):
            self.admin.is_staff = False
            add_users(self.admin, CourseCreatorRole(), self.user)

        with self.assertRaises(PermissionDenied):
            add_users(self.user, CourseCreatorRole(), self.user)

    def test_add_user_to_group_requires_active(self):
        with self.assertRaises(PermissionDenied):
            self.admin.is_active = False
            add_users(self.admin, CourseCreatorRole(), self.user)

    def test_add_user_to_group_requires_authenticated(self):
        with self.assertRaises(PermissionDenied):
            with mock.patch(
                'django.contrib.auth.models.User.is_authenticated',
                new_callable=mock.PropertyMock
            ) as mock_is_auth:
                mock_is_auth.return_value = False
                add_users(self.admin, CourseCreatorRole(), self.user)

    def test_remove_user_from_group_requires_staff_access(self):
        with self.assertRaises(PermissionDenied):
            self.admin.is_staff = False
            remove_users(self.admin, CourseCreatorRole(), self.user)

    def test_remove_user_from_group_requires_active(self):
        with self.assertRaises(PermissionDenied):
            self.admin.is_active = False
            remove_users(self.admin, CourseCreatorRole(), self.user)

    def test_remove_user_from_group_requires_authenticated(self):
        with self.assertRaises(PermissionDenied):
            with mock.patch(
                'django.contrib.auth.models.User.is_authenticated',
                new_callable=mock.PropertyMock
            ) as mock_is_auth:
                mock_is_auth.return_value = False
                remove_users(self.admin, CourseCreatorRole(), self.user)


class CCXCourseGroupTest(TestCase):
    """
    Test that access to a CCX course in Studio is disallowed
    """
    def setUp(self):
        """
        Set up test variables
        """
        super(CCXCourseGroupTest, self).setUp()
        self.global_admin = AdminFactory()
        self.staff = User.objects.create_user('teststaff', 'teststaff+courses@edx.org', 'foo')
        self.ccx_course_key = CCXLocator.from_string('ccx-v1:edX+DemoX+Demo_Course+ccx@1')
        add_users(self.global_admin, CourseStaffRole(self.ccx_course_key), self.staff)

    def test_no_global_admin_write_access(self):
        """
        Test that global admins have no write access
        """
        self.assertFalse(has_studio_write_access(self.global_admin, self.ccx_course_key))

    def test_no_staff_write_access(self):
        """
        Test that course staff have no write access
        """
        self.assertFalse(has_studio_write_access(self.staff, self.ccx_course_key))

    def test_no_global_admin_read_access(self):
        """
        Test that global admins have no read access
        """
        self.assertFalse(has_studio_read_access(self.global_admin, self.ccx_course_key))

    def test_no_staff_read_access(self):
        """
        Test that course staff have no read access
        """
        self.assertFalse(has_studio_read_access(self.staff, self.ccx_course_key))


class CourseGroupTest(TestCase):
    """
    Tests for instructor and staff groups for a particular course.
    """

    def setUp(self):
        """ Test case setup """
        super(CourseGroupTest, self).setUp()
        self.global_admin = AdminFactory()
        self.creator = User.objects.create_user('testcreator', 'testcreator+courses@edx.org', 'foo')
        self.staff = User.objects.create_user('teststaff', 'teststaff+courses@edx.org', 'foo')
        self.course_key = CourseLocator('mitX', '101', 'test')

    def test_add_user_to_course_group(self):
        """
        Tests adding user to course group (happy path).
        """
        # Create groups for a new course (and assign instructor role to the creator).
        self.assertFalse(user_has_role(self.creator, CourseInstructorRole(self.course_key)))
        add_users(self.global_admin, CourseInstructorRole(self.course_key), self.creator)
        add_users(self.global_admin, CourseStaffRole(self.course_key), self.creator)
        self.assertTrue(user_has_role(self.creator, CourseInstructorRole(self.course_key)))

        # Add another user to the staff role.
        self.assertFalse(user_has_role(self.staff, CourseStaffRole(self.course_key)))
        add_users(self.creator, CourseStaffRole(self.course_key), self.staff)
        self.assertTrue(user_has_role(self.staff, CourseStaffRole(self.course_key)))

    def test_add_user_to_course_group_permission_denied(self):
        """
        Verifies PermissionDenied if caller of add_user_to_course_group is not instructor role.
        """
        add_users(self.global_admin, CourseInstructorRole(self.course_key), self.creator)
        add_users(self.global_admin, CourseStaffRole(self.course_key), self.creator)
        with self.assertRaises(PermissionDenied):
            add_users(self.staff, CourseStaffRole(self.course_key), self.staff)

    def test_remove_user_from_course_group(self):
        """
        Tests removing user from course group (happy path).
        """
        add_users(self.global_admin, CourseInstructorRole(self.course_key), self.creator)
        add_users(self.global_admin, CourseStaffRole(self.course_key), self.creator)

        add_users(self.creator, CourseStaffRole(self.course_key), self.staff)
        self.assertTrue(user_has_role(self.staff, CourseStaffRole(self.course_key)))

        remove_users(self.creator, CourseStaffRole(self.course_key), self.staff)
        self.assertFalse(user_has_role(self.staff, CourseStaffRole(self.course_key)))

        remove_users(self.creator, CourseInstructorRole(self.course_key), self.creator)
        self.assertFalse(user_has_role(self.creator, CourseInstructorRole(self.course_key)))

    def test_remove_user_from_course_group_permission_denied(self):
        """
        Verifies PermissionDenied if caller of remove_user_from_course_group is not instructor role.
        """
        add_users(self.global_admin, CourseInstructorRole(self.course_key), self.creator)
        another_staff = User.objects.create_user('another', 'teststaff+anothercourses@edx.org', 'foo')
        add_users(self.global_admin, CourseStaffRole(self.course_key), self.creator, self.staff, another_staff)
        with self.assertRaises(PermissionDenied):
            remove_users(self.staff, CourseStaffRole(self.course_key), another_staff)
