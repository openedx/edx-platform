"""
Tests for OAuth token exchange views
"""

# pylint: disable=no-member


import json
import unittest
from datetime import timedelta
import pytest

import ddt
import httpretty
import mock
from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from oauth2_provider.models import Application
from rest_framework.test import APIClient
from social_django.models import Partial

from openedx.core.djangoapps.oauth_dispatch.tests import factories as dot_factories
from common.djangoapps.student.tests.factories import UserFactory
from common.djangoapps.third_party_auth.tests.utils import ThirdPartyOAuthTestMixinFacebook, ThirdPartyOAuthTestMixinGoogle

from .mixins import DOTAdapterMixin
from .utils import TPA_FEATURE_ENABLED, TPA_FEATURES_KEY, AccessTokenExchangeTestMixin


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

    def _assert_error(self, data, expected_error, expected_error_description, error_code=None):
        response = self.csrf_client.post(self.url, data)
        self.assertEqual(response.status_code, error_code if error_code else 400)
        self.assertEqual(response["Content-Type"], "application/json")
        expected_data = {u"error": expected_error, u"error_description": expected_error_description}
        if error_code:
            expected_data['error_code'] = error_code
        self.assertEqual(
            json.loads(response.content.decode('utf-8')),
            expected_data
        )

    def _assert_success(self, data, expected_scopes):
        response = self.csrf_client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        content = json.loads(response.content.decode('utf-8'))
        self.assertEqual(set(content.keys()), self.get_token_response_keys())
        self.assertEqual(content["token_type"], "Bearer")
        self.assertLessEqual(
            timedelta(seconds=int(content["expires_in"])),
            timedelta(days=30)
        )
        actual_scopes = content["scope"]
        if actual_scopes:
            actual_scopes = actual_scopes.split(' ')
        else:
            actual_scopes = []
        self.assertEqual(set(actual_scopes), set(expected_scopes))
        token = self.oauth2_adapter.get_access_token(token_string=content["access_token"])
        self.assertEqual(token.user, self.user)
        self.assertEqual(self.oauth2_adapter.get_client_for_token(token), self.oauth_client)
        self.assertEqual(set(self.oauth2_adapter.get_token_scope_names(token)), set(expected_scopes))

    def test_single_access_token(self):
        def extract_token(response):
            """
            Returns the access token from the response payload.
            """
            return json.loads(response.content.decode('utf-8'))["access_token"]

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
            json.loads(response.content.decode('utf-8')),
            {
                "error": "invalid_request",
                "error_description": "Only POST requests allowed.",
            }
        )

    def test_invalid_provider(self):
        url = reverse("exchange_access_token", kwargs={"backend": "invalid"})
        response = self.client.post(url, self.data)
        self.assertEqual(response.status_code, 404)

    @pytest.mark.skip(reason="this is very entangled with dop use in third_party_auth")
    def test_invalid_client(self):
        """TODO(jinder): this test overwrites function of same name in mixin
        Remove when dop has been removed from third party auth
        (currently underlying code used dop adapter, which is no longer supported by auth_exchange)
        """
        pass

    @pytest.mark.skip(reason="this is very entangled with dop use in third_party_auth")
    def test_missing_fields(self):
        """TODO(jinder): this test overwrites function of same name in mixin
        Remove when dop has been removed from third party auth
        (currently underlying code used dop adapter, which is no longer supported by auth_exchange)
        """
        pass

    def test_disabled_user(self):
        """
        Test if response status code is correct in case of disabled user.
        """
        self.user.set_unusable_password()
        self.user.save()
        self._setup_provider_response(success=True)
        self._assert_error(self.data, "account_disabled", "user account is disabled", 403)


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
        self.oauth2_client = Application.objects.create(client_type=Application.CLIENT_CONFIDENTIAL)

    def _verify_response(self, access_token, expected_status_code, expected_cookie_name=None):
        """
        Calls the login_with_access_token endpoint and verifies the response given the expected values.
        """
        url = reverse("login_with_access_token")
        response = self.client.post(url, HTTP_AUTHORIZATION=u"Bearer {0}".format(access_token).encode('utf-8'))
        self.assertEqual(response.status_code, expected_status_code)
        if expected_cookie_name:
            self.assertIn(expected_cookie_name, response.cookies)

    def _create_dot_access_token(self, grant_type='Client credentials'):
        """
        Create dot based access token
        """
        dot_application = dot_factories.ApplicationFactory(user=self.user, authorization_grant_type=grant_type)
        return dot_factories.AccessTokenFactory(user=self.user, application=dot_application)

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
