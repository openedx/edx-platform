""" Test Student helpers """


import logging

import ddt
import unittest
from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from mock import patch
from mock import Mock
from testfixtures import LogCapture

from student.tests.factories import UserFactory

if not settings.TAHOE_TEMP_MONKEYPATCHING_JUNIPER_TESTS:  # TODO: Refactor or fix in RED-1674
    # TODO: Fix broken imports See https://openedx.atlassian.net/browse/DEPR-47
    from edx_oauth2_provider.models import TrustedClient
    from edx_oauth2_provider.tests.factories import (
        TrustedClientFactory,
        AccessTokenFactory,
        ClientFactory,
        RefreshTokenFactory,
    )

    from provider.constants import CONFIDENTIAL, PUBLIC
    from oauth2_provider.models import AccessToken, RefreshToken
    from openedx.core.djangoapps.oauth_dispatch.api import destroy_oauth_tokens

from openedx.core.djangoapps.site_configuration.tests.test_util import with_site_configuration_context
from student.helpers import get_next_url_for_login_page

LOGGER_NAME = "student.helpers"


@ddt.ddt
class TestLoginHelper(TestCase):
    """Test login helper methods."""
    static_url = settings.STATIC_URL

    def setUp(self):
        super(TestLoginHelper, self).setUp()
        self.request = RequestFactory()

    @staticmethod
    def _add_session(request):
        """Annotate the request object with a session"""
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()

    @ddt.data(
        (logging.WARNING, "WARNING", "https://www.amazon.com", "text/html", None,
         "Unsafe redirect parameter detected after login page: 'https://www.amazon.com'"),
        # TODO: Fix the test case below. Likely broken because of our theme fixes -- Omar
        #      (logging.WARNING, "WARNING", "testserver/edx.org/images/logo", "text/html", None,
        #       "Redirect to theme content detected after login page: 'testserver/edx.org/images/logo'"),
        (logging.INFO, "INFO", "favicon.ico", "image/*", "test/agent",
         "Redirect to non html content 'image/*' detected from 'test/agent' after login page: 'favicon.ico'"),
        (logging.WARNING, "WARNING", "https://www.test.com/test.jpg", "image/*", None,
         "Unsafe redirect parameter detected after login page: 'https://www.test.com/test.jpg'"),
        (logging.INFO, "INFO", static_url + "dummy.png", "image/*", "test/agent",
         "Redirect to non html content 'image/*' detected from 'test/agent' after login page: '" + static_url +
         "dummy.png" + "'"),
        (logging.WARNING, "WARNING", "test.png", "text/html", None,
         "Redirect to url path with specified filed type 'image/png' not allowed: 'test.png'"),
        (logging.WARNING, "WARNING", static_url + "dummy.png", "text/html", None,
         "Redirect to url path with specified filed type 'image/png' not allowed: '" + static_url + "dummy.png" + "'"),
    )
    @ddt.unpack
    def test_next_failures(self, log_level, log_name, unsafe_url, http_accept, user_agent, expected_log):
        """ Test unsafe next parameter """
        with LogCapture(LOGGER_NAME, level=log_level) as logger:
            req = self.request.get(settings.LOGIN_URL + "?next={url}".format(url=unsafe_url))
            req.META["HTTP_ACCEPT"] = http_accept
            req.META["HTTP_USER_AGENT"] = user_agent
            get_next_url_for_login_page(req)
            logger.check(
                (LOGGER_NAME, log_name, expected_log)
            )

    @ddt.data(
        ('/dashboard', 'text/html', 'testserver'),
        ('https://edx.org/courses', 'text/*', 'edx.org'),
        ('https://test.edx.org/courses', '*/*', 'edx.org'),
        ('https://test2.edx.org/courses', 'image/webp, */*;q=0.8', 'edx.org'),
    )
    @ddt.unpack
    @override_settings(LOGIN_REDIRECT_WHITELIST=['test.edx.org', 'test2.edx.org'])
    def test_safe_next(self, next_url, http_accept, host):
        """ Test safe next parameter """
        req = self.request.get(settings.LOGIN_URL + "?next={url}".format(url=next_url), HTTP_HOST=host)
        req.META["HTTP_ACCEPT"] = http_accept
        next_page = get_next_url_for_login_page(req)
        self.assertEqual(next_page, next_url)

    tpa_hint_test_cases = [
        # Test requests outside the TPA pipeline - tpa_hint should be added.
        (None, '/dashboard', '/dashboard', False),
        ('', '/dashboard', '/dashboard', False),
        ('', '/dashboard?tpa_hint=oa2-google-oauth2', '/dashboard?tpa_hint=oa2-google-oauth2', False),
        # TODO: Fix ('saml-idp', '/dashboard', '/dashboard?tpa_hint=saml-idp', False). This test is likely to be
        #       broken because of our SAML customizations -- Omar
        # THIRD_PARTY_AUTH_HINT can be overridden via the query string
        ('saml-idp', '/dashboard?tpa_hint=oa2-google-oauth2', '/dashboard?tpa_hint=oa2-google-oauth2', False),

        # Test requests inside the TPA pipeline - tpa_hint should not be added, preventing infinite loop.
        (None, '/dashboard', '/dashboard', True),
        ('', '/dashboard', '/dashboard', True),
        ('', '/dashboard?tpa_hint=oa2-google-oauth2', '/dashboard?tpa_hint=oa2-google-oauth2', True),
        ('saml-idp', '/dashboard', '/dashboard', True),
        # OK to leave tpa_hint overrides in place.
        ('saml-idp', '/dashboard?tpa_hint=oa2-google-oauth2', '/dashboard?tpa_hint=oa2-google-oauth2', True),
    ]
    tpa_hint_test_cases_with_method = [
        (method, *test_case)
        for test_case in tpa_hint_test_cases
        for method in ['GET', 'POST']
    ]

    @patch('student.helpers.third_party_auth.pipeline.get')
    @ddt.data(*tpa_hint_test_cases_with_method)
    @ddt.unpack
    def test_third_party_auth_hint(
        self,
        method,
        tpa_hint,
        next_url,
        expected_url,
        running_pipeline,
        mock_running_pipeline,
    ):
        mock_running_pipeline.return_value = running_pipeline

        def validate_login():
            """
            Assert that get_next_url_for_login_page returns as expected.
            """
            if method == 'GET':
                req = self.request.get(settings.LOGIN_URL + "?next={url}".format(url=next_url))
            elif method == 'POST':
                req = self.request.post(settings.LOGIN_URL, {'next': next_url})
            req.META["HTTP_ACCEPT"] = "text/html"
            self._add_session(req)
            next_page = get_next_url_for_login_page(req)
            self.assertEqual(next_page, expected_url)

        with override_settings(FEATURES=dict(settings.FEATURES, THIRD_PARTY_AUTH_HINT=tpa_hint)):
            validate_login()

        with with_site_configuration_context(configuration=dict(THIRD_PARTY_AUTH_HINT=tpa_hint)):
            validate_login()

    @patch('student.helpers._get_redirect_to', Mock(return_value=None))
    def test_custom_tahoe_site_redirect_lms(self):
        """
        Allow site admins to customize the default after-login URL.

        Appsembler: This is specific to Tahoe and mostly not suitable for contribution to upstream.
        """
        request = Mock(GET={}, POST={})
        assert '/dashboard' == get_next_url_for_login_page(request), 'Default should be /dashboard'

        with with_site_configuration_context(configuration={
            'LOGIN_REDIRECT_URL': '/about'
        }):
            assert '/about' == get_next_url_for_login_page(request), 'Custom redirect should be used'

        with with_site_configuration_context(configuration={
            'LOGIN_REDIRECT_URL': ''  # Falsy or empty URLs should not be used
        }):
            assert '/dashboard' == get_next_url_for_login_page(request), 'Falsy url should default to dashboard'


@unittest.skipIf(
    settings.TAHOE_TEMP_MONKEYPATCHING_JUNIPER_TESTS,  # TODO: Refactor or fix in RED-1674
    'edX removed TrustedClient See https://openedx.atlassian.net/browse/DEPR-47'
)
class TestDestroyOAuthTokensHelper(TestCase):
    def setUp(self):
        super(TestDestroyOAuthTokensHelper, self).setUp()
        self.user = UserFactory.create()
        self.client = ClientFactory(logout_uri='https://amc.example.com/logout/', client_type=CONFIDENTIAL)
        access_token = AccessTokenFactory.create(user=self.user, client=self.client)
        RefreshTokenFactory.create(user=self.user, client=self.client, access_token=access_token)

    def assert_destroy_behaviour(self, should_be_kept, message):
        """
        Helper to test the `destroy_oauth_tokens` behaviour.
        """
        assert AccessToken.objects.count()  # Sanity check
        assert RefreshToken.objects.count()  # Sanity check
        destroy_oauth_tokens(self.user)
        assert should_be_kept == AccessToken.objects.count(), message
        assert should_be_kept == RefreshToken.objects.count(), message

    @patch.dict(settings.FEATURES, {'KEEP_TRUSTED_CONFIDENTIAL_CLIENT_TOKENS': False})
    def test_confidential_trusted_client_feature_disabled(self):
        """
        Tokens that have a confidential TrustedClient should be removed if the feature is disabled
        """
        TrustedClientFactory.create(client=self.client)
        self.assert_destroy_behaviour(
            should_be_kept=False,
            message='Tokens of a trusted confidential client should be deleted if the feature is disabled',
        )

    @patch.dict(settings.FEATURES, {'KEEP_TRUSTED_CONFIDENTIAL_CLIENT_TOKENS': True})
    def test_confidential_trusted_client(self):
        """
        Tokens that have a confidential TrustedClient shouldn't be removed.
        """
        TrustedClientFactory.create(client=self.client)
        self.assert_destroy_behaviour(
            should_be_kept=True,
            message='Tokens of a trusted confidential client should be kept',
        )

    @patch.dict(settings.FEATURES, {'KEEP_TRUSTED_CONFIDENTIAL_CLIENT_TOKENS': True})
    def test_no_trusted_client(self):
        """
        Only tokens that don't have a TrustedClient should be removed.
        """
        assert not TrustedClient.objects.count()  # 'Sanity check, there should not be a client'
        self.assert_destroy_behaviour(
            should_be_kept=False,
            message='Tokens of an untrusted client should be deleted',
        )

    @patch.dict(settings.FEATURES, {'KEEP_TRUSTED_CONFIDENTIAL_CLIENT_TOKENS': True})
    def test_public_trusted_client(self):
        """
        Tokens for public clients are removed, even if they're trusted.
        """
        self.client.client_type = PUBLIC
        self.client.save()
        TrustedClientFactory.create(client=self.client)
        self.assert_destroy_behaviour(
            should_be_kept=False,
            message='Tokens of a public trusted client should be deleted',
        )
