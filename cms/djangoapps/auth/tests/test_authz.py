"""
Tests authz.py
"""
import mock

from django.test import TestCase
from django.contrib.auth.models import User

from auth.authz import add_user_to_creator_group, remove_user_from_creator_group, is_user_in_creator_group

class CreatorGroupTest(TestCase):
    """
    Tests for the course creator group.
    """
    def setUp(self):
        """ Test case setup """
        self.user = User.objects.create_user('testuser', 'test+courses@edx.org', 'foo')

    def test_creator_group_not_enabled(self):
        """
        Tests that is_user_in_creator_group always returns True if ENABLE_CREATOR_GROUP
        and DISABLE_COURSE_CREATION are both not turned on.
        """
        self.assertTrue(is_user_in_creator_group(self.user))

    def test_creator_group_enabled_but_empty(self):
        """ Tests creator group feature on, but group empty. """
        with mock.patch.dict('django.conf.settings.MITX_FEATURES', {"ENABLE_CREATOR_GROUP" : True}):
            self.assertFalse(is_user_in_creator_group(self.user))

            # Make user staff. This will cause is_user_in_creator_group to return True.
            self.user.is_staff = True
            self.assertTrue(is_user_in_creator_group(self.user))

    def test_creator_group_enabled_nonempty(self):
        """ Tests creator group feature on, user added. """
        with mock.patch.dict('django.conf.settings.MITX_FEATURES', {"ENABLE_CREATOR_GROUP" : True}):
            self.assertTrue(add_user_to_creator_group(self.user))
            self.assertTrue(is_user_in_creator_group(self.user))

            # check that a user who has not been added to the group still returns false
            user_not_added = User.objects.create_user('testuser2', 'test+courses2@edx.org', 'foo2')
            self.assertFalse(is_user_in_creator_group(user_not_added))

            # remove first user from the group and verify that is_user_in_creator_group now returns false
            remove_user_from_creator_group(self.user)
            self.assertFalse(is_user_in_creator_group(self.user))

    def test_add_user_not_authenticated(self):
        """
        Tests that adding to creator group fails if user is not authenticated
        """
        self.user.is_authenticated = False
        self.assertFalse(add_user_to_creator_group(self.user))

    def test_add_user_not_active(self):
        """
        Tests that adding to creator group fails if user is not active
        """
        self.user.is_active = False
        self.assertFalse(add_user_to_creator_group(self.user))

    def test_course_creation_disabled(self):
        """ Tests that the COURSE_CREATION_DISABLED flag overrides course creator group settings. """
        with mock.patch.dict('django.conf.settings.MITX_FEATURES', {'DISABLE_COURSE_CREATION': True, "ENABLE_CREATOR_GROUP" : True}):
            # Add user to creator group.
            self.assertTrue(add_user_to_creator_group(self.user))

            # DISABLE_COURSE_CREATION overrides (user is not marked as staff).
            self.assertFalse(is_user_in_creator_group(self.user))

            # Mark as staff. Now is_user_in_creator_group returns true.
            self.user.is_staff = True
            self.assertTrue(is_user_in_creator_group(self.user))

            # Remove user from creator group. is_user_in_creator_group still returns true because is_staff=True
            remove_user_from_creator_group(self.user)
            self.assertTrue(is_user_in_creator_group(self.user))
