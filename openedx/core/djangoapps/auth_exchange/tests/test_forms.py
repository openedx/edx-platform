# pylint: disable=no-member
"""
Tests for OAuth token exchange forms
"""
import unittest

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import TestCase
from django.test.client import RequestFactory
import httpretty
from provider import scope
from social_django.models import Partial
import social_django.utils as social_utils

from third_party_auth.tests.utils import ThirdPartyOAuthTestMixinFacebook, ThirdPartyOAuthTestMixinGoogle

from ..forms import AccessTokenExchangeForm
from .utils import AccessTokenExchangeTestMixin, TPA_FEATURE_ENABLED, TPA_FEATURES_KEY
from .mixins import DOPAdapterMixin, DOTAdapterMixin


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

    def tearDown(self):
        super(AccessTokenExchangeFormTest, self).tearDown()
        Partial.objects.all().delete()

    def _assert_error(self, data, expected_error, expected_error_description):
        form = AccessTokenExchangeForm(request=self.request, oauth2_adapter=self.oauth2_adapter, data=data)
        self.assertEqual(
            form.errors,
            {"error": expected_error, "error_description": expected_error_description}
        )

    def _assert_success(self, data, expected_scopes):
        form = AccessTokenExchangeForm(request=self.request, oauth2_adapter=self.oauth2_adapter, data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["user"], self.user)
        self.assertEqual(form.cleaned_data["client"], self.oauth_client)
        self.assertEqual(scope.to_names(form.cleaned_data["scope"]), expected_scopes)


# This is necessary because cms does not implement third party auth
@unittest.skipUnless(TPA_FEATURE_ENABLED, TPA_FEATURES_KEY + " not enabled")
@httpretty.activate
class DOPAccessTokenExchangeFormTestFacebook(
        DOPAdapterMixin,
        AccessTokenExchangeFormTest,
        ThirdPartyOAuthTestMixinFacebook,
        TestCase,
):
    """
    Tests for AccessTokenExchangeForm used with Facebook, tested against
    django-oauth2-provider (DOP).
    """
    pass


# This is necessary because cms does not implement third party auth
@unittest.skipUnless(TPA_FEATURE_ENABLED, TPA_FEATURES_KEY + " not enabled")
@httpretty.activate
class DOTAccessTokenExchangeFormTestFacebook(
        DOTAdapterMixin,
        AccessTokenExchangeFormTest,
        ThirdPartyOAuthTestMixinFacebook,
        TestCase,
):
    """
    Tests for AccessTokenExchangeForm used with Facebook, tested against
    django-oauth-toolkit (DOT).
    """
    pass


# This is necessary because cms does not implement third party auth
@unittest.skipUnless(TPA_FEATURE_ENABLED, TPA_FEATURES_KEY + " not enabled")
@httpretty.activate
class DOPAccessTokenExchangeFormTestGoogle(
        DOPAdapterMixin,
        AccessTokenExchangeFormTest,
        ThirdPartyOAuthTestMixinGoogle,
        TestCase,
):
    """
    Tests for AccessTokenExchangeForm used with Google, tested against
    django-oauth2-provider (DOP).
    """
    pass


# This is necessary because cms does not implement third party auth
@unittest.skipUnless(TPA_FEATURE_ENABLED, TPA_FEATURES_KEY + " not enabled")
@httpretty.activate
class DOTAccessTokenExchangeFormTestGoogle(
        DOTAdapterMixin,
        AccessTokenExchangeFormTest,
        ThirdPartyOAuthTestMixinGoogle,
        TestCase,
):
    """
    Tests for AccessTokenExchangeForm used with Google, tested against
    django-oauth-toolkit (DOT).
    """
    pass
