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
        self.enabled_provider = self.configure_google_provider(enabled=True)


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
            pipeline.get_authenticated_user(self.enabled_provider, 'new_' + self.user.username, 'user@example.com')

    def test_raises_does_not_exist_if_user_found_but_no_association(self):
        backend_name = 'backend'

        self.assertIsNotNone(self.get_by_username(self.user.username))
        self.assertFalse(any(provider.Registry.get_enabled_by_backend_name(backend_name)))

        with self.assertRaises(models.User.DoesNotExist):
            pipeline.get_authenticated_user(self.enabled_provider, self.user.username, 'user@example.com')

    def test_raises_does_not_exist_if_user_and_association_found_but_no_match(self):
        self.assertIsNotNone(self.get_by_username(self.user.username))
        social_models.DjangoStorage.user.create_social_auth(
            self.user, 'uid', 'other_' + self.enabled_provider.backend_name)

        with self.assertRaises(models.User.DoesNotExist):
            pipeline.get_authenticated_user(self.enabled_provider, self.user.username, 'uid')

    def test_returns_user_with_is_authenticated_and_backend_set_if_match(self):
        social_models.DjangoStorage.user.create_social_auth(self.user, 'uid', self.enabled_provider.backend_name)
        user = pipeline.get_authenticated_user(self.enabled_provider, self.user.username, 'uid')

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
        self.assertFalse(provider.Registry.enabled())
        self.assertEquals([], pipeline.get_provider_user_states(self.user))

    def test_state_not_returned_for_disabled_provider(self):
        disabled_provider = self.configure_google_provider(enabled=False)
        enabled_provider = self.configure_facebook_provider(enabled=True)
        social_models.DjangoStorage.user.create_social_auth(self.user, 'uid', disabled_provider.backend_name)
        states = pipeline.get_provider_user_states(self.user)

        self.assertEqual(1, len(states))
        self.assertNotIn(disabled_provider.provider_id, (state.provider.provider_id for state in states))
        self.assertIn(enabled_provider.provider_id, (state.provider.provider_id for state in states))

    def test_states_for_enabled_providers_user_has_accounts_associated_with(self):
        # Enable two providers - Google and LinkedIn:
        google_provider = self.configure_google_provider(enabled=True)
        linkedin_provider = self.configure_linkedin_provider(enabled=True)
        user_social_auth_google = social_models.DjangoStorage.user.create_social_auth(
            self.user, 'uid', google_provider.backend_name)
        user_social_auth_linkedin = social_models.DjangoStorage.user.create_social_auth(
            self.user, 'uid', linkedin_provider.backend_name)
        states = pipeline.get_provider_user_states(self.user)

        self.assertEqual(2, len(states))

        google_state = [state for state in states if state.provider.provider_id == google_provider.provider_id][0]
        linkedin_state = [state for state in states if state.provider.provider_id == linkedin_provider.provider_id][0]

        self.assertTrue(google_state.has_account)
        self.assertEqual(google_provider.provider_id, google_state.provider.provider_id)
        # Also check the row ID. Note this 'id' changes whenever the configuration does:
        self.assertEqual(google_provider.id, google_state.provider.id)  # pylint: disable=no-member
        self.assertEqual(self.user, google_state.user)
        self.assertEqual(user_social_auth_google.id, google_state.association_id)

        self.assertTrue(linkedin_state.has_account)
        self.assertEqual(linkedin_provider.provider_id, linkedin_state.provider.provider_id)
        self.assertEqual(linkedin_provider.id, linkedin_state.provider.id)  # pylint: disable=no-member
        self.assertEqual(self.user, linkedin_state.user)
        self.assertEqual(user_social_auth_linkedin.id, linkedin_state.association_id)

    def test_states_for_enabled_providers_user_has_no_account_associated_with(self):
        # Enable two providers - Google and LinkedIn:
        google_provider = self.configure_google_provider(enabled=True)
        linkedin_provider = self.configure_linkedin_provider(enabled=True)
        self.assertEqual(len(provider.Registry.enabled()), 2)

        states = pipeline.get_provider_user_states(self.user)

        self.assertEqual([], [x for x in social_models.DjangoStorage.user.objects.all()])
        self.assertEqual(2, len(states))

        google_state = [state for state in states if state.provider.provider_id == google_provider.provider_id][0]
        linkedin_state = [state for state in states if state.provider.provider_id == linkedin_provider.provider_id][0]

        self.assertFalse(google_state.has_account)
        self.assertEqual(google_provider.provider_id, google_state.provider.provider_id)
        # Also check the row ID. Note this 'id' changes whenever the configuration does:
        self.assertEqual(google_provider.id, google_state.provider.id)  # pylint: disable=no-member
        self.assertEqual(self.user, google_state.user)

        self.assertFalse(linkedin_state.has_account)
        self.assertEqual(linkedin_provider.provider_id, linkedin_state.provider.provider_id)
        self.assertEqual(linkedin_provider.id, linkedin_state.provider.id)  # pylint: disable=no-member
        self.assertEqual(self.user, linkedin_state.user)


@unittest.skipUnless(
    testutil.AUTH_FEATURES_KEY in settings.FEATURES, testutil.AUTH_FEATURES_KEY + ' not in settings.FEATURES')
class UrlFormationTestCase(TestCase):
    """Tests formation of URLs for pipeline hook points."""

    def test_complete_url_raises_value_error_if_provider_not_enabled(self):
        provider_name = 'oa2-not-enabled'

        self.assertIsNone(provider.Registry.get(provider_name))

        with self.assertRaises(ValueError):
            pipeline.get_complete_url(provider_name)

    def test_complete_url_returns_expected_format(self):
        complete_url = pipeline.get_complete_url(self.enabled_provider.backend_name)

        self.assertTrue(complete_url.startswith('/auth/complete'))
        self.assertIn(self.enabled_provider.backend_name, complete_url)

    def test_disconnect_url_raises_value_error_if_provider_not_enabled(self):
        provider_name = 'oa2-not-enabled'

        self.assertIsNone(provider.Registry.get(provider_name))

        with self.assertRaises(ValueError):
            pipeline.get_disconnect_url(provider_name, 1000)

    def test_disconnect_url_returns_expected_format(self):
        disconnect_url = pipeline.get_disconnect_url(self.enabled_provider.provider_id, 1000)
        disconnect_url = disconnect_url.rstrip('?')
        self.assertEqual(
            disconnect_url,
            '/auth/disconnect/{backend}/{association_id}/'.format(
                backend=self.enabled_provider.backend_name, association_id=1000)
        )

    def test_login_url_raises_value_error_if_provider_not_enabled(self):
        provider_id = 'oa2-not-enabled'

        self.assertIsNone(provider.Registry.get(provider_id))

        with self.assertRaises(ValueError):
            pipeline.get_login_url(provider_id, pipeline.AUTH_ENTRY_LOGIN)

    def test_login_url_returns_expected_format(self):
        login_url = pipeline.get_login_url(self.enabled_provider.provider_id, pipeline.AUTH_ENTRY_LOGIN)

        self.assertTrue(login_url.startswith('/auth/login'))
        self.assertIn(self.enabled_provider.backend_name, login_url)
        self.assertTrue(login_url.endswith(pipeline.AUTH_ENTRY_LOGIN))

    def test_for_value_error_if_provider_id_invalid(self):
        provider_id = 'invalid'  # Format is normally "{prefix}-{identifier}"

        with self.assertRaises(ValueError):
            provider.Registry.get(provider_id)

        with self.assertRaises(ValueError):
            pipeline.get_login_url(provider_id, pipeline.AUTH_ENTRY_LOGIN)

        with self.assertRaises(ValueError):
            pipeline.get_disconnect_url(provider_id, 1000)

        with self.assertRaises(ValueError):
            pipeline.get_complete_url(provider_id)
