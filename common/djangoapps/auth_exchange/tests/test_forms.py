# pylint: disable=no-member
"""
Tests for OAuth token exchange forms
"""
import unittest

from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import TestCase
from django.test.client import RequestFactory
import httpretty
from provider import scope
import social.apps.django_app.utils as social_utils

from auth_exchange.forms import AccessTokenExchangeForm
from auth_exchange.tests.utils import AccessTokenExchangeTestMixin
from third_party_auth.tests.utils import ThirdPartyOAuthTestMixinFacebook, ThirdPartyOAuthTestMixinGoogle


class AccessTokenExchangeFormTest(AccessTokenExchangeTestMixin):
    """
    Mixin that defines test cases for AccessTokenExchangeForm
    """
    def setUp(self):
        super(AccessTokenExchangeFormTest, self).setUp()
        self.request = RequestFactory().post("dummy_url")
        redirect_uri = 'dummy_redirect_url'
        SessionMiddleware().process_request(self.request)
        self.request.social_strategy = social_utils.load_strategy(self.request)
        # pylint: disable=no-member
        self.request.backend = social_utils.load_backend(self.request.social_strategy, self.BACKEND, redirect_uri)

    def _assert_error(self, data, expected_error, expected_error_description):
        form = AccessTokenExchangeForm(request=self.request, data=data)
        self.assertEqual(
            form.errors,
            {"error": expected_error, "error_description": expected_error_description}
        )
        self.assertNotIn("partial_pipeline", self.request.session)

    def _assert_success(self, data, expected_scopes):
        form = AccessTokenExchangeForm(request=self.request, data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["user"], self.user)
        self.assertEqual(form.cleaned_data["client"], self.oauth_client)
        self.assertEqual(scope.to_names(form.cleaned_data["scope"]), expected_scopes)


# This is necessary because cms does not implement third party auth
@unittest.skipUnless(settings.FEATURES.get("ENABLE_THIRD_PARTY_AUTH"), "third party auth not enabled")
@httpretty.activate
class AccessTokenExchangeFormTestFacebook(
        AccessTokenExchangeFormTest,
        ThirdPartyOAuthTestMixinFacebook,
        TestCase
):
    """
    Tests for AccessTokenExchangeForm used with Facebook
    """
    pass


# This is necessary because cms does not implement third party auth
@unittest.skipUnless(settings.FEATURES.get("ENABLE_THIRD_PARTY_AUTH"), "third party auth not enabled")
@httpretty.activate
class AccessTokenExchangeFormTestGoogle(
        AccessTokenExchangeFormTest,
        ThirdPartyOAuthTestMixinGoogle,
        TestCase
):
    """
    Tests for AccessTokenExchangeForm used with Google
    """
    pass
