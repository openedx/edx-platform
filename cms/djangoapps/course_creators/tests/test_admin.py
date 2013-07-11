"""
Tests course_creators.admin.py.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.admin.sites import AdminSite
from django.http import HttpRequest
import mock

from course_creators.admin import CourseCreatorAdmin
from course_creators.models import CourseCreator
from auth.authz import is_user_in_creator_group


class CourseCreatorAdminTest(TestCase):
    """
    Tests for course creator admin.
    """

    def setUp(self):
        """ Test case setup """
        self.user = User.objects.create_user('test_user', 'test_user+courses@edx.org', 'foo')
        self.table_entry = CourseCreator(user=self.user)
        self.table_entry.save()

        self.admin = User.objects.create_user('Mark', 'admin+courses@edx.org', 'foo')
        self.admin.is_staff = True

        self.request = HttpRequest()
        self.request.user = self.admin

        self.creator_admin = CourseCreatorAdmin(self.table_entry, AdminSite())

    def test_change_status(self):
        """
        Tests that updates to state impact the creator group maintained in authz.py.
        """
        def change_state(state, is_creator):
            """ Helper method for changing state """
            self.table_entry.state = state
            self.creator_admin.save_model(self.request, self.table_entry, None, True)
            self.assertEqual(is_creator, is_user_in_creator_group(self.user))

        with mock.patch.dict('django.conf.settings.MITX_FEATURES', {"ENABLE_CREATOR_GROUP": True}):
            # User is initially unrequested.
            self.assertFalse(is_user_in_creator_group(self.user))

            change_state(CourseCreator.GRANTED, True)

            change_state(CourseCreator.DENIED, False)

            change_state(CourseCreator.GRANTED, True)

            change_state(CourseCreator.PENDING, False)

            change_state(CourseCreator.GRANTED, True)

            change_state(CourseCreator.UNREQUESTED, False)

    def test_add_permission(self):
        """
        Tests that staff cannot add entries
        """
        self.assertFalse(self.creator_admin.has_add_permission(self.request))

    def test_delete_permission(self):
        """
        Tests that staff cannot delete entries
        """
        self.assertFalse(self.creator_admin.has_delete_permission(self.request))

    def test_change_permission(self):
        """
        Tests that only staff can change entries
        """
        self.assertTrue(self.creator_admin.has_change_permission(self.request))

        self.request.user = self.user
        self.assertFalse(self.creator_admin.has_change_permission(self.request))
