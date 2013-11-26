"""
Tests authz.py
"""
import mock

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

from auth.authz import add_user_to_creator_group, remove_user_from_creator_group, is_user_in_creator_group,\
    create_all_course_groups, add_user_to_course_group, STAFF_ROLE_NAME, INSTRUCTOR_ROLE_NAME,\
    is_user_in_course_group_role, remove_user_from_course_group, get_users_with_staff_role,\
    get_users_with_instructor_role


class CreatorGroupTest(TestCase):
    """
    Tests for the course creator group.
    """

    def setUp(self):
        """ Test case setup """
        self.user = User.objects.create_user('testuser', 'test+courses@edx.org', 'foo')
        self.admin = User.objects.create_user('Mark', 'admin+courses@edx.org', 'foo')
        self.admin.is_staff = True

    def test_creator_group_not_enabled(self):
        """
        Tests that is_user_in_creator_group always returns True if ENABLE_CREATOR_GROUP
        and DISABLE_COURSE_CREATION are both not turned on.
        """
        self.assertTrue(is_user_in_creator_group(self.user))

    def test_creator_group_enabled_but_empty(self):
        """ Tests creator group feature on, but group empty. """
        with mock.patch.dict('django.conf.settings.MITX_FEATURES', {"ENABLE_CREATOR_GROUP": True}):
            self.assertFalse(is_user_in_creator_group(self.user))

            # Make user staff. This will cause is_user_in_creator_group to return True.
            self.user.is_staff = True
            self.assertTrue(is_user_in_creator_group(self.user))

    def test_creator_group_enabled_nonempty(self):
        """ Tests creator group feature on, user added. """
        with mock.patch.dict('django.conf.settings.MITX_FEATURES', {"ENABLE_CREATOR_GROUP": True}):
            self.assertTrue(add_user_to_creator_group(self.admin, self.user))
            self.assertTrue(is_user_in_creator_group(self.user))

            # check that a user who has not been added to the group still returns false
            user_not_added = User.objects.create_user('testuser2', 'test+courses2@edx.org', 'foo2')
            self.assertFalse(is_user_in_creator_group(user_not_added))

            # remove first user from the group and verify that is_user_in_creator_group now returns false
            remove_user_from_creator_group(self.admin, self.user)
            self.assertFalse(is_user_in_creator_group(self.user))

    def test_add_user_not_authenticated(self):
        """
        Tests that adding to creator group fails if user is not authenticated
        """
        self.user.is_authenticated = False
        self.assertFalse(add_user_to_creator_group(self.admin, self.user))

    def test_add_user_not_active(self):
        """
        Tests that adding to creator group fails if user is not active
        """
        self.user.is_active = False
        self.assertFalse(add_user_to_creator_group(self.admin, self.user))

    def test_course_creation_disabled(self):
        """ Tests that the COURSE_CREATION_DISABLED flag overrides course creator group settings. """
        with mock.patch.dict('django.conf.settings.MITX_FEATURES',
                             {'DISABLE_COURSE_CREATION': True, "ENABLE_CREATOR_GROUP": True}):
            # Add user to creator group.
            self.assertTrue(add_user_to_creator_group(self.admin, self.user))

            # DISABLE_COURSE_CREATION overrides (user is not marked as staff).
            self.assertFalse(is_user_in_creator_group(self.user))

            # Mark as staff. Now is_user_in_creator_group returns true.
            self.user.is_staff = True
            self.assertTrue(is_user_in_creator_group(self.user))

            # Remove user from creator group. is_user_in_creator_group still returns true because is_staff=True
            remove_user_from_creator_group(self.admin, self.user)
            self.assertTrue(is_user_in_creator_group(self.user))

    def test_add_user_to_group_requires_staff_access(self):
        with self.assertRaises(PermissionDenied):
            self.admin.is_staff = False
            add_user_to_creator_group(self.admin, self.user)

        with self.assertRaises(PermissionDenied):
            add_user_to_creator_group(self.user, self.user)

    def test_add_user_to_group_requires_active(self):
        with self.assertRaises(PermissionDenied):
            self.admin.is_active = False
            add_user_to_creator_group(self.admin, self.user)

    def test_add_user_to_group_requires_authenticated(self):
        with self.assertRaises(PermissionDenied):
            self.admin.is_authenticated = False
            add_user_to_creator_group(self.admin, self.user)

    def test_remove_user_from_group_requires_staff_access(self):
        with self.assertRaises(PermissionDenied):
            self.admin.is_staff = False
            remove_user_from_creator_group(self.admin, self.user)

    def test_remove_user_from_group_requires_active(self):
        with self.assertRaises(PermissionDenied):
            self.admin.is_active = False
            remove_user_from_creator_group(self.admin, self.user)

    def test_remove_user_from_group_requires_authenticated(self):
        with self.assertRaises(PermissionDenied):
            self.admin.is_authenticated = False
            remove_user_from_creator_group(self.admin, self.user)


class CourseGroupTest(TestCase):
    """
    Tests for instructor and staff groups for a particular course.
    """

    def setUp(self):
        """ Test case setup """
        self.creator = User.objects.create_user('testcreator', 'testcreator+courses@edx.org', 'foo')
        self.staff = User.objects.create_user('teststaff', 'teststaff+courses@edx.org', 'foo')
        self.location = 'i4x', 'mitX', '101', 'course', 'test'

    def test_add_user_to_course_group(self):
        """
        Tests adding user to course group (happy path).
        """
        # Create groups for a new course (and assign instructor role to the creator).
        self.assertFalse(is_user_in_course_group_role(self.creator, self.location, INSTRUCTOR_ROLE_NAME))
        create_all_course_groups(self.creator, self.location)
        self.assertTrue(is_user_in_course_group_role(self.creator, self.location, INSTRUCTOR_ROLE_NAME))

        # Add another user to the staff role.
        self.assertFalse(is_user_in_course_group_role(self.staff, self.location, STAFF_ROLE_NAME))
        self.assertTrue(add_user_to_course_group(self.creator, self.staff, self.location, STAFF_ROLE_NAME))
        self.assertTrue(is_user_in_course_group_role(self.staff, self.location, STAFF_ROLE_NAME))

    def test_add_user_to_course_group_permission_denied(self):
        """
        Verifies PermissionDenied if caller of add_user_to_course_group is not instructor role.
        """
        create_all_course_groups(self.creator, self.location)
        with self.assertRaises(PermissionDenied):
            add_user_to_course_group(self.staff, self.staff, self.location, STAFF_ROLE_NAME)

    def test_remove_user_from_course_group(self):
        """
        Tests removing user from course group (happy path).
        """
        create_all_course_groups(self.creator, self.location)

        self.assertTrue(add_user_to_course_group(self.creator, self.staff, self.location, STAFF_ROLE_NAME))
        self.assertTrue(is_user_in_course_group_role(self.staff, self.location, STAFF_ROLE_NAME))

        remove_user_from_course_group(self.creator, self.staff, self.location, STAFF_ROLE_NAME)
        self.assertFalse(is_user_in_course_group_role(self.staff, self.location, STAFF_ROLE_NAME))

        remove_user_from_course_group(self.creator, self.creator, self.location, INSTRUCTOR_ROLE_NAME)
        self.assertFalse(is_user_in_course_group_role(self.creator, self.location, INSTRUCTOR_ROLE_NAME))

    def test_remove_user_from_course_group_permission_denied(self):
        """
        Verifies PermissionDenied if caller of remove_user_from_course_group is not instructor role.
        """
        create_all_course_groups(self.creator, self.location)
        with self.assertRaises(PermissionDenied):
            remove_user_from_course_group(self.staff, self.staff, self.location, STAFF_ROLE_NAME)

    def test_get_staff(self):
        # Do this test with staff in 2 different classes.
        create_all_course_groups(self.creator, self.location)
        add_user_to_course_group(self.creator, self.staff, self.location, STAFF_ROLE_NAME)

        location2 = 'i4x', 'mitX', '103', 'course', 'test2'
        staff2 = User.objects.create_user('teststaff2', 'teststaff2+courses@edx.org', 'foo')
        create_all_course_groups(self.creator, location2)
        add_user_to_course_group(self.creator, staff2, location2, STAFF_ROLE_NAME)

        self.assertSetEqual({self.staff, staff2, self.creator}, get_users_with_staff_role())

    def test_get_instructor(self):
        # Do this test with creators in 2 different classes.
        create_all_course_groups(self.creator, self.location)
        add_user_to_course_group(self.creator, self.staff, self.location, STAFF_ROLE_NAME)

        location2 = 'i4x', 'mitX', '103', 'course', 'test2'
        creator2 = User.objects.create_user('testcreator2', 'testcreator2+courses@edx.org', 'foo')
        staff2 = User.objects.create_user('teststaff2', 'teststaff2+courses@edx.org', 'foo')
        create_all_course_groups(creator2, location2)
        add_user_to_course_group(creator2, staff2, location2, STAFF_ROLE_NAME)

        self.assertSetEqual({self.creator, creator2}, get_users_with_instructor_role())
