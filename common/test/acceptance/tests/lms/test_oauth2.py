# -*- coding: utf-8 -*-
"""Tests for OAuth2 permission delegation."""
from common.test.acceptance.pages.lms.oauth2_confirmation import OAuth2Confirmation
from common.test.acceptance.pages.lms.auto_auth import AutoAuthPage
from bok_choy.web_app_test import WebAppTest

from flaky import flaky

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

        # This redirects to an invalid URI. For chrome verify title, current_url otherwise
        if self.browser.name == 'chrome':
            query = self._qs(self.browser.title)
            self.assertIn('access_denied', query['error'])
        else:
            query = self._qs(self.browser.current_url)
            self.assertIn('access_denied', query['error'])

    @flaky      # TODO, fix this: TNL-4190
    def test_accepting_redirects(self):
        """
        If you accept the request, you're redirected to the redirect_url with
        the correct query params.
        """
        self._auth()
        assert self.oauth_page.visit()

        # This redirects to an invalid URI.
        self.oauth_page.confirm()
        self.oauth_page.wait_for_element_absence('input[name=authorize]', 'Authorization button is not present')

        # Due to a bug in ChromeDriver, when chrome is on invalid URI,self.browser.current_url outputs
        # data:text/html,chromewebdata. When this happens in our case,query string is present in the title.
        # So to get query string, we branch out based on selected browser.
        if self.browser.name == 'chrome':
            query = self._qs(self.browser.title)
        else:
            query = self._qs(self.browser.current_url)

        self.assertIn('code', query)
