"""
Tests course_creators.views.py.
"""

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.test import TestCase, RequestFactory

from course_creators.views import add_user_with_status_unrequested, add_user_with_status_granted
from course_creators.views import get_course_creator_status, update_course_creator_group, user_requested_access
import mock
from student.roles import CourseCreatorRole
from student import auth
from edxmako.tests import mako_middleware_process_request


class CourseCreatorView(TestCase):
    """
    Tests for modifying the course creator table.
    """

    def setUp(self):
        """ Test case setup """
        super(CourseCreatorView, self).setUp()
        self.user = User.objects.create_user('test_user', 'test_user+courses@edx.org', 'foo')
        self.admin = User.objects.create_user('Mark', 'admin+courses@edx.org', 'foo')
        self.admin.is_staff = True

    def test_staff_permission_required(self):
        """
        Tests that any method changing the course creator authz group must be called with staff permissions.
        """
        with self.assertRaises(PermissionDenied):
            add_user_with_status_granted(self.user, self.user)

        with self.assertRaises(PermissionDenied):
            update_course_creator_group(self.user, self.user, True)

    def test_table_initially_empty(self):
        self.assertIsNone(get_course_creator_status(self.user))

    def test_add_unrequested(self):
        add_user_with_status_unrequested(self.user)
        self.assertEqual('unrequested', get_course_creator_status(self.user))

        # Calling add again will be a no-op (even if state is different).
        add_user_with_status_granted(self.admin, self.user)
        self.assertEqual('unrequested', get_course_creator_status(self.user))

    def test_add_granted(self):
        with mock.patch.dict('django.conf.settings.FEATURES', {"ENABLE_CREATOR_GROUP": True}):
            # Calling add_user_with_status_granted impacts is_user_in_course_group_role.
            self.assertFalse(auth.has_access(self.user, CourseCreatorRole()))

            add_user_with_status_granted(self.admin, self.user)
            self.assertEqual('granted', get_course_creator_status(self.user))

            # Calling add again will be a no-op (even if state is different).
            add_user_with_status_unrequested(self.user)
            self.assertEqual('granted', get_course_creator_status(self.user))

            self.assertTrue(auth.has_access(self.user, CourseCreatorRole()))

    def test_update_creator_group(self):
        with mock.patch.dict('django.conf.settings.FEATURES', {"ENABLE_CREATOR_GROUP": True}):
            self.assertFalse(auth.has_access(self.user, CourseCreatorRole()))
            update_course_creator_group(self.admin, self.user, True)
            self.assertTrue(auth.has_access(self.user, CourseCreatorRole()))
            update_course_creator_group(self.admin, self.user, False)
            self.assertFalse(auth.has_access(self.user, CourseCreatorRole()))

    def test_user_requested_access(self):
        add_user_with_status_unrequested(self.user)
        self.assertEqual('unrequested', get_course_creator_status(self.user))

        request = RequestFactory().get('/')
        request.user = self.user

        mako_middleware_process_request(request)
        user_requested_access(self.user)
        self.assertEqual('pending', get_course_creator_status(self.user))

    def test_user_requested_already_granted(self):
        add_user_with_status_granted(self.admin, self.user)
        self.assertEqual('granted', get_course_creator_status(self.user))
        # Will not "downgrade" to pending because that would require removing the
        # user from the authz course creator group (and that can only be done by an admin).
        user_requested_access(self.user)
        self.assertEqual('granted', get_course_creator_status(self.user))

    def test_add_user_unrequested_staff(self):
        # Users marked as is_staff will not be added to the course creator table.
        add_user_with_status_unrequested(self.admin)
        self.assertIsNone(get_course_creator_status(self.admin))

    def test_add_user_granted_staff(self):
        # Users marked as is_staff will not be added to the course creator table.
        add_user_with_status_granted(self.admin, self.admin)
        self.assertIsNone(get_course_creator_status(self.admin))
