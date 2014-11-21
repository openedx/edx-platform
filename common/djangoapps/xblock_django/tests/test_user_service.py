"""
Tests for the DjangoXBlockUserService.
"""
import unittest

from xblock_django.user_service import DjangoXBlockUserService
from student.tests.factories import UserFactory, AnonymousUserFactory


class UserServiceTestCase(unittest.TestCase):
    """
    Tests for the DjangoXBlockUserService.
    """
    def setUp(self):
        self.user = UserFactory(username="tester", email="tester@tester.com")
        self.user.profile.name = "Test Tester"
        self.anon_user = AnonymousUserFactory()

    def assert_is_anon_xb_user(self, xb_user):
        """
        A set of assertions for an anonymous XBlockUser.
        """
        properties = [
            'email',
            'full_name',
            'username',
            'user_id',
        ]
        self.assertFalse(xb_user.is_authenticated)
        for prop in properties:
            # Make default from getattr False instead of None to ensure None is really coming from xb_user.
            self.assertIsNone(getattr(xb_user, prop, False))

    def assert_xblock_user_matches_django(self, xb_user, dj_user):
        """
        A set of assertions for comparing a XBlockUser to a django User
        """
        self.assertTrue(xb_user.is_authenticated)
        self.assertEqual(xb_user.email, dj_user.email)
        self.assertEqual(xb_user.full_name, dj_user.profile.name)
        self.assertEqual(xb_user.username, dj_user.username)
        self.assertEqual(xb_user.user_id, dj_user.id)

    def test_convert_anon_user(self):
        """
        Tests for convert_django_user_to_xblock_user behavior when django user is AnonymousUser.
        """
        django_user_service = DjangoXBlockUserService(self.anon_user)
        xb_user = django_user_service.get_current_user()
        self.assert_is_anon_xb_user(xb_user)

    def test_convert_authenticate_user(self):
        """
        Tests for convert_django_user_to_xblock_user behavior when django user is User.
        """
        django_user_service = DjangoXBlockUserService(self.user)
        xb_user = django_user_service.get_current_user()
        self.assert_xblock_user_matches_django(xb_user, self.user)
