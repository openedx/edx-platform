"""Tests for cached authentication middleware."""
from unittest.mock import call, patch

import django
from django.conf import settings
from django.contrib.auth import SESSION_KEY
from django.contrib.auth.models import AnonymousUser, User  # lint-amnesty, pylint: disable=imported-auth-user
from django.http import HttpResponse, SimpleCookie
from django.test import TestCase
from django.urls import reverse

from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.cache_toolbox.middleware import CacheBackedAuthenticationMiddleware
from openedx.core.djangoapps.safe_sessions.middleware import SafeCookieData, SafeSessionMiddleware
from openedx.core.djangolib.testing.utils import get_mock_request, skip_unless_cms, skip_unless_lms


class CachedAuthMiddlewareTestCase(TestCase):
    """Tests for CacheBackedAuthenticationMiddleware class."""

    def setUp(self):
        super().setUp()
        password = 'test-password'
        self.user = UserFactory(password=password)
        self.client.login(username=self.user.username, password=password)
        self.request = get_mock_request(self.user)
        self.client.response = HttpResponse()
        self.client.response.cookies = SimpleCookie()  # preparing cookies

    def _test_custom_attribute_after_changing_hash(self, test_url, mock_set_custom_attribute):
        """verify that set_custom_attribute is called with expected values"""
        password = 'test-password'

        # Test DEFAULT_HASHING_ALGORITHM of 'sha1' for both login and client get
        with self.settings(DEFAULT_HASHING_ALGORITHM='sha1'):
            self.client.login(username=self.user.username, password=password)
            self.client.get(test_url)
        # For Django 3.2, the setting 'sha1' applies and is the "default".
        # For Django 4, the setting no longer applies, and 'sha256' will be used for both as the "default".
        mock_set_custom_attribute.assert_has_calls([
            call('DEFAULT_HASHING_ALGORITHM', 'sha1'),
            call('session_hash_verified', "default"),
        ])
        mock_set_custom_attribute.reset_mock()

        # Test DEFAULT_HASHING_ALGORITHM of 'sha1' for login and switch to 'sha256' for client get.
        with self.settings(DEFAULT_HASHING_ALGORITHM='sha1'):
            self.client.login(username=self.user.username, password=password)
            with self.settings(DEFAULT_HASHING_ALGORITHM='sha256'):
                self.client.get(test_url)
        if django.VERSION < (4, 0):
            # For Django 3.2, the setting 'sha1' applies to login, and uses 'she256' for client get,
            # and should "fallback" to 'sha1".
            mock_set_custom_attribute.assert_has_calls([
                call('DEFAULT_HASHING_ALGORITHM', 'sha256'),
                call('session_hash_verified', "fallback"),
            ])
        else:
            # For Django 4, the setting no longer applies, and again 'sha256' will be used for both as the "default".
            mock_set_custom_attribute.assert_has_calls([
                call('DEFAULT_HASHING_ALGORITHM', 'sha256'),
                call('session_hash_verified', "default"),
            ])
        mock_set_custom_attribute.reset_mock()

        # Test DEFAULT_HASHING_ALGORITHM of 'sha256' for both login and client get
        with self.settings(DEFAULT_HASHING_ALGORITHM='sha256'):
            self.client.login(username=self.user.username, password=password)
            self.client.get(test_url)
        # For Django 3.2, the setting 'sha256' applies and is the "default".
        # For Django 4, the setting no longer applies, and 'sha256' will be used for both as the "default".
        mock_set_custom_attribute.assert_has_calls([
            call('DEFAULT_HASHING_ALGORITHM', 'sha256'),
            call('session_hash_verified', "default"),
        ])

    @skip_unless_lms
    def test_session_change_lms(self):
        """
        Verify (from the LMS side) that if a user's session auth hash and the request's
        hash differ, the user is logged out.
        """
        dashboard_url = reverse('dashboard')
        response = self.client.get(dashboard_url)
        assert response.status_code == 200

        with patch(
            "openedx.core.djangoapps.cache_toolbox.middleware.set_custom_attribute"
        ) as mock_set_custom_attribute:
            with patch.object(User, 'get_session_auth_hash', return_value='abc123', autospec=True):
                response = self.client.get(dashboard_url)

        redirect_url = reverse('signin_user') + '?next=' + dashboard_url
        self.assertRedirects(response, redirect_url, target_status_code=200)
        mock_set_custom_attribute.assert_any_call('failed_session_verification', True)

    @skip_unless_cms
    def test_session_change_cms(self):
        """
        Verify (from the CMS side) that if a user's session auth hash and the request's
        hash differ, the user is logged out.
        """
        home_url = reverse('home')
        response = self.client.get(home_url)
        assert response.status_code == 302
        assert response.url == "http://course-authoring-mfe/home"

        with patch(
            "openedx.core.djangoapps.cache_toolbox.middleware.set_custom_attribute"
        ) as mock_set_custom_attribute:
            with patch.object(User, 'get_session_auth_hash', return_value='abc123', autospec=True):
                response = self.client.get(home_url)

        redirect_url = settings.LOGIN_URL + '?next=' + home_url
        self.assertRedirects(response, redirect_url, target_status_code=302)
        mock_set_custom_attribute.assert_any_call('failed_session_verification', True)

    @skip_unless_lms
    @patch("openedx.core.djangoapps.cache_toolbox.middleware.set_custom_attribute")
    def test_custom_attribute_after_changing_hash_lms(self, mock_set_custom_attribute):
        """Test set_custom_attribute is called with expected values in LMS"""
        test_url = reverse('dashboard')
        self._test_custom_attribute_after_changing_hash(test_url, mock_set_custom_attribute)

    @skip_unless_cms
    @patch("openedx.core.djangoapps.cache_toolbox.middleware.set_custom_attribute")
    def test_custom_attribute_after_changing_hash_cms(self, mock_set_custom_attribute):
        """Test set_custom_attribute is called with expected values in CMS"""
        test_url = reverse('home')
        self._test_custom_attribute_after_changing_hash(test_url, mock_set_custom_attribute)

    def test_user_logout_on_session_hash_change(self):
        """
        Verify that if a user's session auth hash and the request's hash
        differ, the user is logged out:
         - session is flushed
         - request user is changed to Anonymous user
         - logged in cookies are deleted
        """
        # preparing session and setting cookies
        session_id = self.client.session.session_key
        safe_cookie_data = SafeCookieData.create(session_id, self.user.id)
        self.request.COOKIES[settings.SESSION_COOKIE_NAME] = str(safe_cookie_data)
        self.client.response.cookies[settings.SESSION_COOKIE_NAME] = session_id
        self.client.response.cookies['edx-jwt-cookie-header-payload'] = 'test-jwt-payload'
        SafeSessionMiddleware(get_response=lambda request: None).process_request(self.request)

        # asserts that user, session, and JWT cookies exist
        assert self.request.session.get(SESSION_KEY) is not None
        assert self.request.user != AnonymousUser()
        assert self.client.response.cookies.get(settings.SESSION_COOKIE_NAME).value == session_id
        assert self.client.response.cookies.get('edx-jwt-cookie-header-payload').value == 'test-jwt-payload'

        with patch.object(User, 'get_session_auth_hash', return_value='abc123', autospec=True):
            # Django 3.2 has _legacy_get_session_auth_hash, and Django 4 does not
            # Remove once we reach Django 4
            if hasattr(User, '_legacy_get_session_auth_hash'):
                with patch.object(User, '_legacy_get_session_auth_hash', return_value='abc123'):
                    CacheBackedAuthenticationMiddleware(get_response=lambda request: None).process_request(self.request)

            else:
                CacheBackedAuthenticationMiddleware(get_response=lambda request: None).process_request(self.request)
            SafeSessionMiddleware(get_response=lambda request: None).process_response(
                self.request, self.client.response
            )

        # asserts that user, session, and JWT cookies do not exist
        assert self.request.session.get(SESSION_KEY) is None
        assert self.request.user == AnonymousUser()
        assert self.client.response.cookies.get(settings.SESSION_COOKIE_NAME).value != session_id
        assert self.client.response.cookies.get(settings.SESSION_COOKIE_NAME).value == ""
        assert self.client.response.cookies.get('edx-jwt-cookie-header-payload').value == ""
