# pylint: disable=no-member
"""
Tests for OAuth token exchange views
"""
from datetime import timedelta
import json
import mock
import unittest

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
import httpretty
import provider.constants
from provider import scope
from provider.oauth2.models import AccessToken, Client

from auth_exchange.tests.utils import AccessTokenExchangeTestMixin
from student.tests.factories import UserFactory
from third_party_auth.tests.utils import ThirdPartyOAuthTestMixinFacebook, ThirdPartyOAuthTestMixinGoogle


class AccessTokenExchangeViewTest(AccessTokenExchangeTestMixin):
    """
    Mixin that defines test cases for AccessTokenExchangeView
    """
    def setUp(self):
        super(AccessTokenExchangeViewTest, self).setUp()
        self.url = reverse("exchange_access_token", kwargs={"backend": self.BACKEND})

    def _assert_error(self, data, expected_error, expected_error_description):
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(
            json.loads(response.content),
            {"error": expected_error, "error_description": expected_error_description}
        )
        self.assertNotIn("partial_pipeline", self.client.session)

    def _assert_success(self, data, expected_scopes):
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        content = json.loads(response.content)
        self.assertEqual(set(content.keys()), {"access_token", "token_type", "expires_in", "scope"})
        self.assertEqual(content["token_type"], "Bearer")
        self.assertLessEqual(
            timedelta(seconds=int(content["expires_in"])),
            provider.constants.EXPIRE_DELTA_PUBLIC
        )
        self.assertEqual(content["scope"], " ".join(expected_scopes))
        token = AccessToken.objects.get(token=content["access_token"])
        self.assertEqual(token.user, self.user)
        self.assertEqual(token.client, self.oauth_client)
        self.assertEqual(scope.to_names(token.scope), expected_scopes)

    def test_single_access_token(self):
        def extract_token(response):
            """
            Returns the access token from the response payload.
            """
            return json.loads(response.content)["access_token"]

        self._setup_provider_response(success=True)
        for single_access_token in [True, False]:
            with mock.patch(
                "auth_exchange.views.constants.SINGLE_ACCESS_TOKEN",
                single_access_token
            ):
                first_response = self.client.post(self.url, self.data)
                second_response = self.client.post(self.url, self.data)
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
@unittest.skipUnless(settings.FEATURES.get("ENABLE_THIRD_PARTY_AUTH"), "third party auth not enabled")
@httpretty.activate
class AccessTokenExchangeViewTestFacebook(
        AccessTokenExchangeViewTest,
        ThirdPartyOAuthTestMixinFacebook,
        TestCase
):
    """
    Tests for AccessTokenExchangeView used with Facebook
    """
    pass


# This is necessary because cms does not implement third party auth
@unittest.skipUnless(settings.FEATURES.get("ENABLE_THIRD_PARTY_AUTH"), "third party auth not enabled")
@httpretty.activate
class AccessTokenExchangeViewTestGoogle(
        AccessTokenExchangeViewTest,
        ThirdPartyOAuthTestMixinGoogle,
        TestCase
):
    """
    Tests for AccessTokenExchangeView used with Google
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

    def _verify_response(self, access_token, expected_status_code, expected_num_cookies):
        """
        Calls the login_with_access_token endpoint and verifies the response given the expected values.
        """
        url = reverse("login_with_access_token")
        response = self.client.post(url, HTTP_AUTHORIZATION="Bearer {0}".format(access_token))
        self.assertEqual(response.status_code, expected_status_code)
        self.assertEqual(len(response.cookies), expected_num_cookies)

    def test_success(self):
        access_token = AccessToken.objects.create(
            token="test_access_token",
            client=self.oauth2_client,
            user=self.user,
        )
        self._verify_response(access_token, expected_status_code=204, expected_num_cookies=1)
        self.assertEqual(len(self.client.cookies), 1)
        self.assertEqual(self.client.session['_auth_user_id'], self.user.id)

    def test_unauthenticated(self):
        self._verify_response("invalid_token", expected_status_code=401, expected_num_cookies=0)
        self.assertEqual(len(self.client.cookies), 0)
        self.assertNotIn("session_key", self.client.session)
