"""
Test of custom django-oauth-toolkit behavior
"""

# pylint: disable=protected-access

from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from ..dot_overrides import EdxOAuth2Validator


class AuthenticateTestCase(TestCase):
    """
    Test that users can authenticate with either username or email
    """

    def setUp(self):
        super(AuthenticateTestCase, self).setUp()
        self.user = User.objects.create_user(
            username='darkhelmet',
            password='12345',
            email='darkhelmet@spaceball_one.org',
        )
        self.validator = EdxOAuth2Validator()

    def test_authenticate_with_username(self):
        user = self.validator._authenticate(username='darkhelmet', password='12345')
        self.assertEqual(
            self.user,
            user
        )

    def test_authenticate_with_email(self):
        user = self.validator._authenticate(username='darkhelmet@spaceball_one.org', password='12345')
        self.assertEqual(
            self.user,
            user
        )


class CustomValidationTestCase(TestCase):
    """
    Test custom user validation works.

    In particular, inactive users should be able to validate.
    """
    def setUp(self):
        super(CustomValidationTestCase, self).setUp()
        self.user = User.objects.create_user(
            username='darkhelmet',
            password='12345',
            email='darkhelmet@spaceball_one.org',
        )
        self.validator = EdxOAuth2Validator()
        self.request_factory = RequestFactory()

    def test_active_user_validates(self):
        self.assertTrue(self.user.is_active)
        request = self.request_factory.get('/')
        self.assertTrue(self.validator.validate_user('darkhelmet', '12345', client=None, request=request))

    def test_inactive_user_validates(self):
        self.user.is_active = False
        self.user.save()
        request = self.request_factory.get('/')
        self.assertTrue(self.validator.validate_user('darkhelmet', '12345', client=None, request=request))
