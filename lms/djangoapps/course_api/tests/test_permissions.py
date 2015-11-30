"""
Test authorization functions
"""

import ddt
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from .mixins import CourseApiFactoryMixin
from ..permissions import can_view_courses_for_username, MasqueradingPermission


class ViewCoursesForUsernameTestCase(CourseApiFactoryMixin, TestCase):
    """
    Verify functionality of view_courses_for_username.

    Any user should be able to view their own courses, and staff users
    should be able to view anyone's courses.
    """

    @classmethod
    def setUpClass(cls):
        super(ViewCoursesForUsernameTestCase, cls).setUpClass()
        cls.staff_user = cls.create_user('staff', is_staff=True)
        cls.honor_user = cls.create_user('honor', is_staff=False)
        cls.anonymous_user = AnonymousUser()

    def test_for_staff(self):
        self.assertTrue(can_view_courses_for_username(self.staff_user, self.staff_user.username))

    def test_for_honor(self):
        self.assertTrue(can_view_courses_for_username(self.honor_user, self.honor_user.username))

    def test_for_staff_as_honor(self):
        self.assertTrue(can_view_courses_for_username(self.staff_user, self.honor_user.username))

    def test_for_honor_as_staff(self):
        self.assertFalse(can_view_courses_for_username(self.honor_user, self.staff_user.username))

    def test_for_none_as_staff(self):
        with self.assertRaises(TypeError):
            can_view_courses_for_username(self.staff_user, None)

    def test_for_anonymous(self):
        self.assertTrue(can_view_courses_for_username(self.anonymous_user, self.anonymous_user.username))

    def test_for_anonymous_as_honor(self):
        self.assertFalse(can_view_courses_for_username(self.anonymous_user, self.honor_user.username))


@ddt.ddt
class MasqueradingPermissionTest(CourseApiFactoryMixin, TestCase):
    """
    Test of lms.djangoapps.course_api.permissions.MasqueradingPermission
    """

    @classmethod
    def setUpClass(cls):
        super(MasqueradingPermissionTest, cls).setUpClass()
        cls.staff_user = cls.create_user('staff', is_staff=True)
        cls.honor_user = cls.create_user('honor', is_staff=False)
        cls.anonymous_user = AnonymousUser()

    def setUp(self):
        super(MasqueradingPermissionTest, self).setUp()
        self.request_factory = APIRequestFactory()

    def _build_request(self, user, query_params=None):
        """
        Create a request for the given user, with the specified query_params
        """
        request = self.request_factory.get('/')
        request.user = user
        request.query_params = query_params or {}
        return request

    @ddt.data('staff_user', 'honor_user', 'anonymous_user')
    def test_nonmasquerading(self, user_identifier):
        user = getattr(self, user_identifier)
        request = self._build_request(user)
        self.assertTrue(MasqueradingPermission().has_permission(request, view=APIView()))
        self.assertEqual(request.user, user)

    @ddt.data('staff_user', 'honor_user', 'anonymous_user')
    def test_explicit_self(self, user_identifier):
        user = getattr(self, user_identifier)
        request = self._build_request(user, {'masquerade': user.username})
        self.assertTrue(MasqueradingPermission().has_permission(request, view=APIView()))
        self.assertEqual(request.user, user)

    @ddt.data(
        ('staff_user', 'honor_user', True),
        ('honor_user', 'staff_user', False),
        ('anonymous_user', 'honor_user', False),
    )
    @ddt.unpack
    def test_masquerading(self, user_identifier, target_identifier, is_permission_granted):
        user = getattr(self, user_identifier)
        target_user = getattr(self, target_identifier)
        request = self._build_request(user, {'masquerade': target_user.username})
        self.assertEqual(MasqueradingPermission().has_permission(request, APIView()), is_permission_granted)
        if is_permission_granted:
            self.assertEqual(request.user, target_user)
        else:
            self.assertEqual(request.user, user)

    @ddt.data(
        ('staff_user', 'honor_user', True),
        ('honor_user', 'staff_user', False),
        ('anonymous_user', 'honor_user', False),
    )
    @ddt.unpack
    def test_alternative_param(self, user_identifier, target_identifier, is_permission_granted):
        user = getattr(self, user_identifier)
        target_user = getattr(self, target_identifier)
        view = APIView()
        view.masquerading_param = 'username'
        request = self._build_request(user, {'username': target_user.username})
        self.assertEqual(MasqueradingPermission().has_permission(request, view=view), is_permission_granted)
        if is_permission_granted:
            self.assertEqual(request.user, target_user)
        else:
            self.assertEqual(request.user, user)
