"""
Tests course_creators.views.py.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

from course_creators.views import add_user_with_status_unrequested, add_user_with_status_granted
from course_creators.views import get_course_creator_status, update_course_creator_group
from course_creators.models import CourseCreator
from auth.authz import is_user_in_creator_group
import mock


class CourseCreatorView(TestCase):
    """
    Tests for modifying the course creator table.
    """

    def setUp(self):
        """ Test case setup """
        self.user = User.objects.create_user('test_user', 'test_user+courses@edx.org', 'foo')
        self.admin = User.objects.create_user('Mark', 'admin+courses@edx.org', 'foo')
        self.admin.is_staff = True

    def test_staff_permission_required(self):
        """
        Tests that add methods and course creator group method must be called with staff permissions.
        """
        with self.assertRaises(PermissionDenied):
            add_user_with_status_granted(self.user, self.user)

        with self.assertRaises(PermissionDenied):
            add_user_with_status_unrequested(self.user, self.user)

        with self.assertRaises(PermissionDenied):
            update_course_creator_group(self.user, self.user, True)

    def test_table_initially_empty(self):
        self.assertIsNone(get_course_creator_status(self.user))

    def test_add_unrequested(self):
        add_user_with_status_unrequested(self.admin, self.user)
        self.assertEqual('unrequested', get_course_creator_status(self.user))

        # Calling add again will be a no-op (even if state is different).
        add_user_with_status_granted(self.admin, self.user)
        self.assertEqual('unrequested', get_course_creator_status(self.user))

    def test_add_granted(self):
        with mock.patch.dict('django.conf.settings.MITX_FEATURES', {"ENABLE_CREATOR_GROUP": True}):
            # Calling add_user_with_status_granted impacts is_user_in_course_group_role.
            self.assertFalse(is_user_in_creator_group(self.user))

            add_user_with_status_granted(self.admin, self.user)
            self.assertEqual('granted', get_course_creator_status(self.user))

            # Calling add again will be a no-op (even if state is different).
            add_user_with_status_unrequested(self.admin, self.user)
            self.assertEqual('granted', get_course_creator_status(self.user))

            self.assertTrue(is_user_in_creator_group(self.user))

    def test_update_creator_group(self):
        with mock.patch.dict('django.conf.settings.MITX_FEATURES', {"ENABLE_CREATOR_GROUP": True}):
            self.assertFalse(is_user_in_creator_group(self.user))
            update_course_creator_group(self.admin, self.user, True)
            self.assertTrue(is_user_in_creator_group(self.user))
            update_course_creator_group(self.admin, self.user, False)
            self.assertFalse(is_user_in_creator_group(self.user))
