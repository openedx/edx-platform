"""
Tests for the DjangoXBlockUserService.
"""
from django.test import TestCase
from xblock_django.user_service import (
    DjangoXBlockUserService,
    ATTR_KEY_IS_AUTHENTICATED,
    ATTR_KEY_USER_ID,
    ATTR_KEY_USERNAME,
    ATTR_KEY_USER_IS_STAFF,
    ATTR_KEY_USER_PREFERENCES,
    USER_PREFERENCES_WHITE_LIST,
)
from student.models import anonymous_id_for_user
from student.tests.factories import UserFactory, AnonymousUserFactory
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.user_api.preferences.api import set_user_preference


class UserServiceTestCase(TestCase):
    """
    Tests for the DjangoXBlockUserService.
    """
    def setUp(self):
        super(UserServiceTestCase, self).setUp()
        self.user = UserFactory(username="tester", email="test@tester.com")
        self.user.profile.name = "Test Tester"
        set_user_preference(self.user, 'pref-lang', 'en')
        set_user_preference(self.user, 'time_zone', 'US/Pacific')
        set_user_preference(self.user, 'not_white_listed', 'hidden_value')
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
        self.assertFalse(xb_user.opt_attrs[ATTR_KEY_USER_IS_STAFF])
        self.assertTrue(
            all(
                pref in USER_PREFERENCES_WHITE_LIST
                for pref in xb_user.opt_attrs[ATTR_KEY_USER_PREFERENCES]
            )
        )

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

    def test_get_anonymous_user_id_returns_none_for_non_staff_users(self):
        """
        Tests for anonymous_user_id method to return None if user is Non-Staff.
        """
        django_user_service = DjangoXBlockUserService(self.user, user_is_staff=False)

        anonymous_user_id = django_user_service.get_anonymous_user_id(username=self.user.username, course_id='edx/toy/2012_Fall')
        self.assertIsNone(anonymous_user_id)

    def test_get_anonymous_user_id_returns_none_for_non_existing_users(self):
        """
        Tests for anonymous_user_id method to return None username does not exist in system.
        """
        django_user_service = DjangoXBlockUserService(self.user, user_is_staff=True)

        anonymous_user_id = django_user_service.get_anonymous_user_id(username="No User", course_id='edx/toy/2012_Fall')
        self.assertIsNone(anonymous_user_id)

    def test_get_anonymous_user_id_returns_id_for_existing_users(self):
        """
        Tests for anonymous_user_id method returns anonymous user id for a user.
        """
        course_key = CourseKey.from_string('edX/toy/2012_Fall')
        anon_user_id = anonymous_id_for_user(
            user=self.user,
            course_id=course_key,
            save=True
        )

        django_user_service = DjangoXBlockUserService(self.user, user_is_staff=True)
        anonymous_user_id = django_user_service.get_anonymous_user_id(
            username=self.user.username,
            course_id='edX/toy/2012_Fall'
        )

        self.assertEqual(anonymous_user_id, anon_user_id)
