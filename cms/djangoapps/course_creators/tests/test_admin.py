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
        self.table_entry = CourseCreator(username=self.user.username, email=self.user.email)
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

            # change state to 'g' (granted)
            change_state('g', True)

            # change state to 'd' (denied)
            change_state('d', False)

            # and change state back to 'g' (granted)
            change_state('g', True)

            # change state to 'p' (pending)
            change_state('p', False)

            # and change state back to 'g' (granted)
            change_state('g', True)

            # and change state back to 'u' (unrequested)
            change_state('u', False)


    def test_delete_bad_user(self):
        """
        Tests that users who no longer exist are deleted from the table.
        """
        with mock.patch.dict('django.conf.settings.MITX_FEATURES', {"ENABLE_CREATOR_GROUP": True}):
            self.assertEqual('test_user', self.table_entry.username)
            self.user.delete()
            # Go through the post-save update, which will delete users who no longer exist.
            self.table_entry.state = 'g'
            self.creator_admin.save_model(self.request, self.table_entry, None, True)
            self.assertEqual(None, self.table_entry.username)
