"""
Tests for OAuth token exchange views
"""

# pylint: disable=no-member

from datetime import timedelta
import json
import mock
import unittest

import ddt
from django.conf import settings
from django.urls import reverse
from django.test import TestCase
import httpretty
import provider.constants
from provider.oauth2.models import AccessToken, Client
from rest_framework.test import APIClient
from social_django.models import Partial

from openedx.core.djangoapps.oauth_dispatch.tests import factories as dot_factories
from student.tests.factories import UserFactory
from third_party_auth.tests.utils import ThirdPartyOAuthTestMixinFacebook, ThirdPartyOAuthTestMixinGoogle
from .mixins import DOPAdapterMixin, DOTAdapterMixin
from .utils import AccessTokenExchangeTestMixin, TPA_FEATURE_ENABLED, TPA_FEATURES_KEY


@ddt.ddt
class AccessTokenExchangeViewTest(AccessTokenExchangeTestMixin):
    """
    Mixin that defines test cases for AccessTokenExchangeView
    """
    def setUp(self):
        super(AccessTokenExchangeViewTest, self).setUp()
        self.url = reverse("exchange_access_token", kwargs={"backend": self.BACKEND})
        self.csrf_client = APIClient(enforce_csrf_checks=True)

    def tearDown(self):
        super(AccessTokenExchangeViewTest, self).tearDown()
        Partial.objects.all().delete()

    def _assert_error(self, data, expected_error, expected_error_description):
        response = self.csrf_client.post(self.url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(
            json.loads(response.content),
            {u"error": expected_error, u"error_description": expected_error_description}
        )

    def _assert_success(self, data, expected_scopes):
        response = self.csrf_client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        content = json.loads(response.content)
        self.assertEqual(set(content.keys()), self.get_token_response_keys())
        self.assertEqual(content["token_type"], "Bearer")
        self.assertLessEqual(
            timedelta(seconds=int(content["expires_in"])),
            provider.constants.EXPIRE_DELTA_PUBLIC
        )
        self.assertEqual(content["scope"], ' '.join(expected_scopes))
        token = self.oauth2_adapter.get_access_token(token_string=content["access_token"])
        self.assertEqual(token.user, self.user)
        self.assertEqual(self.oauth2_adapter.get_client_for_token(token), self.oauth_client)
        self.assertEqual(self.oauth2_adapter.get_token_scope_names(token), expected_scopes)

    def test_single_access_token(self):
        def extract_token(response):
            """
            Returns the access token from the response payload.
            """
            return json.loads(response.content)["access_token"]

        self._setup_provider_response(success=True)
        for single_access_token in [True, False]:
            with mock.patch(
                "openedx.core.djangoapps.auth_exchange.views.constants.SINGLE_ACCESS_TOKEN",
                single_access_token,
            ):
                first_response = self.client.post(self.url, self.data)
                second_response = self.client.post(self.url, self.data)
            self.assertEqual(first_response.status_code, 200)
            self.assertEqual(second_response.status_code, 200)
            self.assertEqual(
                extract_token(first_response) == extract_token(second_response),
                single_access_token
            )

    def test_get_method(self):
        response = self.client.get(self.url, self.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            json.loads(response.content),
            {
                "error": "invalid_request",
                "error_description": "Only POST requests allowed.",
            }
        )

    def test_invalid_provider(self):
        url = reverse("exchange_access_token", kwargs={"backend": "invalid"})
        response = self.client.post(url, self.data)
        self.assertEqual(response.status_code, 404)


# This is necessary because cms does not implement third party auth
@unittest.skipUnless(TPA_FEATURE_ENABLED, TPA_FEATURES_KEY + " not enabled")
@httpretty.activate
class DOPAccessTokenExchangeViewTestFacebook(
        DOPAdapterMixin,
        AccessTokenExchangeViewTest,
        ThirdPartyOAuthTestMixinFacebook,
        TestCase,
):
    """
    Tests for AccessTokenExchangeView used with Facebook
    """
    pass


@unittest.skipUnless(TPA_FEATURE_ENABLED, TPA_FEATURES_KEY + " not enabled")
@httpretty.activate
class DOTAccessTokenExchangeViewTestFacebook(
        DOTAdapterMixin,
        AccessTokenExchangeViewTest,
        ThirdPartyOAuthTestMixinFacebook,
        TestCase,
):
    """
    Rerun AccessTokenExchangeViewTestFacebook tests against DOT backend
    """
    pass


# This is necessary because cms does not implement third party auth
@unittest.skipUnless(TPA_FEATURE_ENABLED, TPA_FEATURES_KEY + " not enabled")
@httpretty.activate
class DOPAccessTokenExchangeViewTestGoogle(
        DOPAdapterMixin,
        AccessTokenExchangeViewTest,
        ThirdPartyOAuthTestMixinGoogle,
        TestCase,
):
    """
    Tests for AccessTokenExchangeView used with Google using
    django-oauth2-provider backend.
    """
    pass


# This is necessary because cms does not implement third party auth
@unittest.skipUnless(TPA_FEATURE_ENABLED, TPA_FEATURES_KEY + " not enabled")
@httpretty.activate
class DOTAccessTokenExchangeViewTestGoogle(
        DOTAdapterMixin,
        AccessTokenExchangeViewTest,
        ThirdPartyOAuthTestMixinGoogle,
        TestCase,
):
    """
    Tests for AccessTokenExchangeView used with Google using
    django-oauth-toolkit backend.
    """
    pass


@unittest.skipUnless(settings.FEATURES.get("ENABLE_OAUTH2_PROVIDER"), "OAuth2 not enabled")
class TestLoginWithAccessTokenView(TestCase):
    """
    Tests for LoginWithAccessTokenView
    """
    def setUp(self):
        super(TestLoginWithAccessTokenView, self).setUp()
        self.user = UserFactory()
        self.oauth2_client = Client.objects.create(client_type=provider.constants.CONFIDENTIAL)

    def _verify_response(self, access_token, expected_status_code, expected_cookie_name=None):
        """
        Calls the login_with_access_token endpoint and verifies the response given the expected values.
        """
        url = reverse("login_with_access_token")
        response = self.client.post(url, HTTP_AUTHORIZATION="Bearer {0}".format(access_token))
        self.assertEqual(response.status_code, expected_status_code)
        if expected_cookie_name:
            self.assertIn(expected_cookie_name, response.cookies)

    def _create_dot_access_token(self, grant_type='Client credentials'):
        """
        Create dot based access token
        """
        dot_application = dot_factories.ApplicationFactory(user=self.user, authorization_grant_type=grant_type)
        return dot_factories.AccessTokenFactory(user=self.user, application=dot_application)

    def _create_dop_access_token(self):
        """
        Create dop based access token
        """
        return AccessToken.objects.create(
            token="test_access_token",
            client=self.oauth2_client,
            user=self.user,
        )

    def test_dop_unsupported(self):
        access_token = self._create_dop_access_token()
        self._verify_response(access_token, expected_status_code=401)

    def test_invalid_token(self):
        self._verify_response("invalid_token", expected_status_code=401)
        self.assertNotIn("session_key", self.client.session)

    def test_dot_password_grant_supported(self):
        access_token = self._create_dot_access_token(grant_type='password')

        self._verify_response(access_token, expected_status_code=204, expected_cookie_name='sessionid')
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.id)

    def test_dot_client_credentials_unsupported(self):
        access_token = self._create_dot_access_token()
        self._verify_response(access_token, expected_status_code=401)
