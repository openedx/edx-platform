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

        def check_redirect():
            """
            Checks that the page correctly redirects to a url with a
            denied query param.
            """
            query = self._qs(self.browser.current_url)
            return 'access_denied' in query['error']

        def check_redirect_chrome():
            """
            Similar to `check_redirect`, but, due to a bug in ChromeDriver,
            we use `self.browser.title` here instead of `self.browser.current_url`
            """
            query = self._qs(self.browser.title)
            return 'access_denied' in query['error']

        # This redirects to an invalid URI. For chrome verify title, current_url otherwise
        if self.browser.name == 'chrome':
            self.oauth_page.wait_for(check_redirect_chrome, 'redirected to invalid URL (chrome)')
        else:
            self.oauth_page.wait_for(check_redirect, 'redirected to invalid URL')

    def test_accepting_redirects(self):
        """
        If you accept the request, you're redirected to the redirect_url with
        the correct query params.
        """
        self._auth()
        assert self.oauth_page.visit()

        # This redirects to an invalid URI.
        self.oauth_page.confirm()
        self.oauth_page.wait_for_element_absence(
            'input[name=authorize]', 'Authorization button is not present'
        )

        def check_query_string():
            """
            Checks that 'code' appears in the browser's current url.
            """
            query = self._qs(self.browser.current_url)
            return 'code' in query

        def check_query_string_chrome():
            """
            Similar to check_query_string, but, due to a bug in ChromeDriver,
            when chrome is on an invalid URI, `self.browser.current_url` outputs
            "data:text/html,chromewebdata" instead of the current URI.

            However, since the query string is present in the `title`, we use
            that for chrome.
            """
            query = self._qs(self.browser.title)
            return 'code' in query

        if self.browser.name == 'chrome':
            self.oauth_page.wait_for(
                check_query_string_chrome, 'redirected with correct query parameters (chrome)'
            )
        else:
            self.oauth_page.wait_for(
                check_query_string, 'redirected with correct query parameters'
            )
