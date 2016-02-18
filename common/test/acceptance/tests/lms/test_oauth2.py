# -*- coding: utf-8 -*-
"""Tests for OAuth2 permission delegation."""
from common.test.acceptance.pages.lms.oauth2_confirmation import OAuth2Confirmation
from common.test.acceptance.pages.lms.auto_auth import AutoAuthPage
from bok_choy.web_app_test import WebAppTest

from urlparse import urlparse, parse_qsl


class OAuth2PermissionDelegationTests(WebAppTest):
    """
    Tests for acceptance/denial of permission delegation requests.
    """

    def setUp(self):
        super(OAuth2PermissionDelegationTests, self).setUp()
        self.oauth_page = OAuth2Confirmation(self.browser)

    def _auth(self):
        """Authenticate the user."""
        AutoAuthPage(self.browser).visit()

    def _qs(self, url):
        """Parse url's querystring into a dict."""
        return dict(parse_qsl(urlparse(url).query))

    def test_error_for_invalid_scopes(self):
        """Requests for invalid scopes throw errors."""
        self._auth()
        self.oauth_page.scopes = ('email', 'does-not-exist')
        assert self.oauth_page.visit()

        self.assertTrue(self.oauth_page.has_error)
        self.assertIn('not a valid scope', self.oauth_page.error_message)

    def test_cancelling_redirects(self):
        """
        If you cancel the request, you're redirected to the redirect_url with a
        denied query param.
        """
        self._auth()
        assert self.oauth_page.visit()
        self.oauth_page.cancel()

        # This redirects to an invalid URI.
        query = self._qs(self.browser.current_url)
        self.assertEqual('access_denied', query['error'])

    def test_accepting_redirects(self):
        """
        If you accept the request, you're redirected to the redirect_url with
        the correct query params.
        """
        self._auth()
        assert self.oauth_page.visit()
        self.oauth_page.confirm()

        # This redirects to an invalid URI.
        query = self._qs(self.browser.current_url)
        self.assertIn('code', query)
