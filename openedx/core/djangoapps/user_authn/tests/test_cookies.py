# pylint: disable=missing-docstring
from __future__ import unicode_literals

from mock import MagicMock
import six
from django.conf import settings
from django.http import HttpResponse
from django.urls import reverse
from django.test import RequestFactory, TestCase

from edx_rest_framework_extensions.auth.jwt.middleware import JwtAuthCookieMiddleware
from openedx.core.djangoapps.user_authn import cookies as cookies_api
from openedx.core.djangoapps.user_authn.tests.utils import setup_login_oauth_client
from openedx.core.djangoapps.user_api.accounts.utils import retrieve_last_sitewide_block_completed
from student.models import CourseEnrollment
from student.tests.factories import UserFactory, AnonymousUserFactory


class CookieTests(TestCase):
    def setUp(self):
        super(CookieTests, self).setUp()
        self.user = UserFactory.create()
        self.request = RequestFactory().get('/')
        self.request.user = self.user
        self.request.session = self._get_stub_session()

    def _get_stub_session(self, expire_at_browser_close=False, max_age=604800):
        return MagicMock(
            get_expire_at_browser_close=lambda: expire_at_browser_close,
            get_expiry_age=lambda: max_age,
        )

    def _get_expected_header_urls(self):
        expected_header_urls = {
            'logout': reverse('logout'),
            'resume_block': retrieve_last_sitewide_block_completed(self.user)
        }

        # Studio (CMS) does not have the URLs below
        if settings.ROOT_URLCONF == 'lms.urls':
            expected_header_urls.update({
                'account_settings': reverse('account_settings'),
                'learner_profile': reverse('learner_profile', kwargs={'username': self.user.username}),
            })

        # Convert relative URL paths to absolute URIs
        for url_name, url_path in six.iteritems(expected_header_urls):
            expected_header_urls[url_name] = self.request.build_absolute_uri(url_path)

        return expected_header_urls

    def _copy_cookies_to_request(self, response, request):
        request.COOKIES = {
            key: val.value
            for key, val in response.cookies.iteritems()
        }

    def _assert_recreate_jwt_from_cookies(self, response, can_recreate):
        """
        Verifies that a JWT can be properly recreated from the 2 separate
        JWT-related cookies using the JwtAuthCookieMiddleware middleware.
        """
        self.request.COOKIES = response.cookies
        JwtAuthCookieMiddleware().process_request(self.request)
        self.assertEqual(
            cookies_api.jwt_cookies.jwt_cookie_name() in self.request.COOKIES,
            can_recreate,
        )

    def _assert_cookies_present(self, response, expected_cookies):
        self.assertSetEqual(set(response.cookies.keys()), set(expected_cookies))

    def test_get_user_info_cookie_data(self):
        actual = cookies_api._get_user_info_cookie_data(self.request, self.user)  # pylint: disable=protected-access

        expected = {
            'version': settings.EDXMKTG_USER_INFO_COOKIE_VERSION,
            'username': self.user.username,
            'header_urls': self._get_expected_header_urls(),
            'enrollmentStatusHash': CourseEnrollment.generate_enrollment_status_hash(self.user)
        }

        self.assertDictEqual(actual, expected)

    def test_set_logged_in_cookies_anonymous_user(self):
        anonymous_user = AnonymousUserFactory()
        response = cookies_api.set_logged_in_cookies(self.request, HttpResponse(), anonymous_user)
        self._assert_cookies_present(response, [])

    def test_set_logged_in_deprecated_cookies(self):
        response = cookies_api.set_logged_in_cookies(self.request, HttpResponse(), self.user)
        self._assert_cookies_present(response, cookies_api.DEPRECATED_LOGGED_IN_COOKIE_NAMES)
        self._assert_recreate_jwt_from_cookies(response, can_recreate=False)

    def test_set_logged_in_jwt_cookies(self):
        setup_login_oauth_client()
        with cookies_api.JWT_COOKIES_FLAG.override(True):
            response = cookies_api.set_logged_in_cookies(self.request, HttpResponse(), self.user)
            self._assert_cookies_present(response, cookies_api.ALL_LOGGED_IN_COOKIE_NAMES)
            self._assert_recreate_jwt_from_cookies(response, can_recreate=True)

    def test_delete_and_is_logged_in_cookie_set(self):
        response = cookies_api.set_logged_in_cookies(self.request, HttpResponse(), self.user)
        self._copy_cookies_to_request(response, self.request)
        self.assertTrue(cookies_api.is_logged_in_cookie_set(self.request))

        cookies_api.delete_logged_in_cookies(response)
        self._copy_cookies_to_request(response, self.request)
        self.assertFalse(cookies_api.is_logged_in_cookie_set(self.request))

    def test_refresh_jwt_cookies(self):
        def _get_refresh_token_value(response):
            return response.cookies[cookies_api.jwt_cookies.jwt_refresh_cookie_name()].value

        setup_login_oauth_client()
        with cookies_api.JWT_COOKIES_FLAG.override(True):
            response = cookies_api.set_logged_in_cookies(self.request, HttpResponse(), self.user)
            self._copy_cookies_to_request(response, self.request)

            new_response = cookies_api.refresh_jwt_cookies(self.request, HttpResponse())
            self._assert_recreate_jwt_from_cookies(new_response, can_recreate=True)
            self.assertNotEqual(
                _get_refresh_token_value(response),
                _get_refresh_token_value(new_response),
            )
