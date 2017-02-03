"""
Test authorization functions
"""

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from .mixins import CourseApiFactoryMixin

from ..permissions import can_view_courses_for_username


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
