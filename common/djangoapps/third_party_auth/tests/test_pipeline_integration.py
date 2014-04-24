"""Integration tests for pipeline.py."""

import unittest

from django.conf import settings
from django import test
from django.contrib.auth import models

from third_party_auth import pipeline, provider
from third_party_auth.tests import testutil
from social.apps.django_app.default import models as social_models


# Get Django User model by reference from python-social-auth. Not a type
# constant, pylint.
User = social_models.DjangoStorage.user.user_model()  # pylint: disable-msg=invalid-name


class TestCase(testutil.TestCase, test.TestCase):
    """Base test case."""

    def setUp(self):
        super(TestCase, self).setUp()
        self.enabled_provider_name = provider.GoogleOauth2.NAME
        provider.Registry.configure_once([self.enabled_provider_name])
        self.enabled_provider = provider.Registry.get(self.enabled_provider_name)


@unittest.skipUnless(
    testutil.AUTH_FEATURES_KEY in settings.FEATURES, testutil.AUTH_FEATURES_KEY + ' not in settings.FEATURES')
class GetAuthenticatedUserTestCase(TestCase):
    """Tests for get_authenticated_user."""

    def setUp(self):
        super(GetAuthenticatedUserTestCase, self).setUp()
        self.user = social_models.DjangoStorage.user.create_user(username='username', password='password')

    def get_by_username(self, username):
        """Gets a User by username."""
        return social_models.DjangoStorage.user.user_model().objects.get(username=username)

    def test_raises_does_not_exist_if_user_missing(self):
        with self.assertRaises(models.User.DoesNotExist):
            pipeline.get_authenticated_user('new_' + self.user.username, 'backend')

    def test_raises_does_not_exist_if_user_found_but_no_association(self):
        backend_name = 'backend'

        self.assertIsNotNone(self.get_by_username(self.user.username))
        self.assertIsNone(provider.Registry.get_by_backend_name(backend_name))

        with self.assertRaises(models.User.DoesNotExist):
            pipeline.get_authenticated_user(self.user.username, 'backend')

    def test_raises_does_not_exist_if_user_and_association_found_but_no_match(self):
        self.assertIsNotNone(self.get_by_username(self.user.username))
        social_models.DjangoStorage.user.create_social_auth(
            self.user, 'uid', 'other_' + self.enabled_provider.BACKEND_CLASS.name)

        with self.assertRaises(models.User.DoesNotExist):
            pipeline.get_authenticated_user(self.user.username, self.enabled_provider.BACKEND_CLASS.name)

    def test_returns_user_with_is_authenticated_and_backend_set_if_match(self):
        social_models.DjangoStorage.user.create_social_auth(self.user, 'uid', self.enabled_provider.BACKEND_CLASS.name)
        user = pipeline.get_authenticated_user(self.user.username, self.enabled_provider.BACKEND_CLASS.name)

        self.assertEqual(self.user, user)
        self.assertEqual(self.enabled_provider.get_authentication_backend(), user.backend)


@unittest.skipUnless(
    testutil.AUTH_FEATURES_KEY in settings.FEATURES, testutil.AUTH_FEATURES_KEY + ' not in settings.FEATURES')
class UrlFormationTestCase(TestCase):
    """Tests formation of URLs for pipeline hook points."""

    def test_complete_url_raises_value_error_if_provider_not_enabled(self):
        provider_name = 'not_enabled'

        self.assertIsNone(provider.Registry.get(provider_name))

        with self.assertRaises(ValueError):
            pipeline.get_complete_url(provider_name)

    def test_complete_url_returns_expected_format(self):
        complete_url = pipeline.get_complete_url(self.enabled_provider.BACKEND_CLASS.name)

        self.assertTrue(complete_url.startswith('/auth/complete'))
        self.assertIn(self.enabled_provider.BACKEND_CLASS.name, complete_url)

    def test_login_url_raises_value_error_if_provider_not_enabled(self):
        provider_name = 'not_enabled'

        self.assertIsNone(provider.Registry.get(provider_name))

        with self.assertRaises(ValueError):
            pipeline.get_login_url(provider_name, pipeline.AUTH_ENTRY_LOGIN)

    def test_login_url_returns_expected_format(self):
        login_url = pipeline.get_login_url(self.enabled_provider.NAME, pipeline.AUTH_ENTRY_LOGIN)

        self.assertTrue(login_url.startswith('/auth/login'))
        self.assertIn(self.enabled_provider.BACKEND_CLASS.name, login_url)
        self.assertTrue(login_url.endswith(pipeline.AUTH_ENTRY_LOGIN))
