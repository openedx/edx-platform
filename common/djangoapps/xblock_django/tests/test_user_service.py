"""
Tests for the DjangoXBlockUserService.
"""
from django.test import TestCase
from xblock_django.user_service import (
    DjangoXBlockUserService,
    ATTR_KEY_IS_AUTHENTICATED,
    ATTR_KEY_USER_ID,
    ATTR_KEY_USERNAME,
)
from student.tests.factories import UserFactory, AnonymousUserFactory


class UserServiceTestCase(TestCase):
    """
    Tests for the DjangoXBlockUserService.
    """
    def setUp(self):
        self.user = UserFactory(username="tester", email="test@tester.com")
        self.user.profile.name = "Test Tester"
        self.anon_user = AnonymousUserFactory()

    def assert_is_anon_xb_user(self, xb_user):
        """
        A set of assertions for an anonymous XBlockUser.
        """
        self.assertFalse(xb_user.opt_attrs[ATTR_KEY_IS_AUTHENTICATED])
        self.assertIsNone(xb_user.full_name)
        self.assertListEqual(xb_user.emails, [])

    def assert_xblock_user_matches_django(self, xb_user, dj_user):
        """
        A set of assertions for comparing a XBlockUser to a django User
        """
        self.assertTrue(xb_user.opt_attrs[ATTR_KEY_IS_AUTHENTICATED])
        self.assertEqual(xb_user.emails[0], dj_user.email)
        self.assertEqual(xb_user.full_name, dj_user.profile.name)
        self.assertEqual(xb_user.opt_attrs[ATTR_KEY_USERNAME], dj_user.username)
        self.assertEqual(xb_user.opt_attrs[ATTR_KEY_USER_ID], dj_user.id)

    def test_convert_anon_user(self):
        """
        Tests for convert_django_user_to_xblock_user behavior when django user is AnonymousUser.
        """
        django_user_service = DjangoXBlockUserService(self.anon_user)
        xb_user = django_user_service.get_current_user()
        self.assertTrue(xb_user.is_current_user)
        self.assert_is_anon_xb_user(xb_user)

    def test_convert_authenticate_user(self):
        """
        Tests for convert_django_user_to_xblock_user behavior when django user is User.
        """
        django_user_service = DjangoXBlockUserService(self.user)
        xb_user = django_user_service.get_current_user()
        self.assertTrue(xb_user.is_current_user)
        self.assert_xblock_user_matches_django(xb_user, self.user)
