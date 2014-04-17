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
class GetProviderUserStatesTestCase(testutil.TestCase, test.TestCase):
    """Tests generation of ProviderUserStates."""

    def setUp(self):
        super(GetProviderUserStatesTestCase, self).setUp()
        self.user = social_models.DjangoStorage.user.create_user(username='username', password='password')

    def test_returns_empty_list_if_no_enabled_providers(self):
        provider.Registry.configure_once([])
        self.assertEquals([], pipeline.get_provider_user_states(self.user))

    def test_state_not_returned_for_disabled_provider(self):
        disabled_provider = provider.GoogleOauth2
        enabled_provider = provider.LinkedInOauth2
        provider.Registry.configure_once([enabled_provider.NAME])
        social_models.DjangoStorage.user.create_social_auth(self.user, 'uid', disabled_provider.BACKEND_CLASS.name)
        states = pipeline.get_provider_user_states(self.user)

        self.assertEqual(1, len(states))
        self.assertNotIn(disabled_provider, (state.provider for state in states))

    def test_states_for_enabled_providers_user_has_accounts_associated_with(self):
        provider.Registry.configure_once([provider.GoogleOauth2.NAME, provider.LinkedInOauth2.NAME])
        social_models.DjangoStorage.user.create_social_auth(self.user, 'uid', provider.GoogleOauth2.BACKEND_CLASS.name)
        social_models.DjangoStorage.user.create_social_auth(
            self.user, 'uid', provider.LinkedInOauth2.BACKEND_CLASS.name)
        states = pipeline.get_provider_user_states(self.user)

        self.assertEqual(2, len(states))

        google_state = [state for state in states if state.provider == provider.GoogleOauth2][0]
        linkedin_state = [state for state in states if state.provider == provider.LinkedInOauth2][0]

        self.assertTrue(google_state.has_account)
        self.assertEqual(provider.GoogleOauth2, google_state.provider)
        self.assertEqual(self.user, google_state.user)

        self.assertTrue(linkedin_state.has_account)
        self.assertEqual(provider.LinkedInOauth2, linkedin_state.provider)
        self.assertEqual(self.user, linkedin_state.user)

    def test_states_for_enabled_providers_user_has_no_account_associated_with(self):
        provider.Registry.configure_once([provider.GoogleOauth2.NAME, provider.LinkedInOauth2.NAME])
        states = pipeline.get_provider_user_states(self.user)

        self.assertEqual([], [x for x in social_models.DjangoStorage.user.objects.all()])
        self.assertEqual(2, len(states))

        google_state = [state for state in states if state.provider == provider.GoogleOauth2][0]
        linkedin_state = [state for state in states if state.provider == provider.LinkedInOauth2][0]

        self.assertFalse(google_state.has_account)
        self.assertEqual(provider.GoogleOauth2, google_state.provider)
        self.assertEqual(self.user, google_state.user)

        self.assertFalse(linkedin_state.has_account)
        self.assertEqual(provider.LinkedInOauth2, linkedin_state.provider)
        self.assertEqual(self.user, linkedin_state.user)


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

    def test_disconnect_url_raises_value_error_if_provider_not_enabled(self):
        provider_name = 'not_enabled'

        self.assertIsNone(provider.Registry.get(provider_name))

        with self.assertRaises(ValueError):
            pipeline.get_disconnect_url(provider_name)

    def test_disconnect_url_returns_expected_format(self):
        disconnect_url = pipeline.get_disconnect_url(self.enabled_provider.NAME)

        self.assertTrue(disconnect_url.startswith('/auth/disconnect'))
        self.assertIn(self.enabled_provider.BACKEND_CLASS.name, disconnect_url)

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
