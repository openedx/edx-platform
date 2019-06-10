# pylint: disable=missing-docstring
from __future__ import unicode_literals

import itertools

import ddt
from mock import MagicMock, patch
import six
from django.conf import settings
from django.http import HttpResponse
from django.urls import reverse
from django.test import RequestFactory, TestCase

from edx_rest_framework_extensions.auth.jwt.decoder import jwt_decode_handler
from edx_rest_framework_extensions.auth.jwt.middleware import JwtAuthCookieMiddleware
from openedx.core.djangoapps.user_authn import cookies as cookies_api
from openedx.core.djangoapps.user_authn.tests.utils import setup_login_oauth_client
from openedx.core.djangoapps.user_api.accounts.utils import retrieve_last_sitewide_block_completed
from student.models import CourseEnrollment
from student.tests.factories import UserFactory, AnonymousUserFactory


@ddt.ddt
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

    def _set_use_jwt_cookie_header(self, request):
        request.META['HTTP_USE_JWT_COOKIE'] = 'true'

    def _assert_recreate_jwt_from_cookies(self, response, can_recreate):
        """
        If can_recreate is True, verifies that a JWT can be properly recreated
        from the 2 separate JWT-related cookies using the
        JwtAuthCookieMiddleware middleware and returns the recreated JWT.
        If can_recreate is False, verifies that a JWT cannot be recreated.
        """
        self._copy_cookies_to_request(response, self.request)
        JwtAuthCookieMiddleware().process_request(self.request)
        self.assertEqual(
            cookies_api.jwt_cookies.jwt_cookie_name() in self.request.COOKIES,
            can_recreate,
        )
        if can_recreate:
            jwt_string = self.request.COOKIES[cookies_api.jwt_cookies.jwt_cookie_name()]
            jwt = jwt_decode_handler(jwt_string)
            self.assertEqual(jwt['scopes'], ['email', 'profile'])

    def _assert_cookies_present(self, response, expected_cookies):
        """ Verify all expected_cookies are present in the response. """
        self.assertSetEqual(set(response.cookies.keys()), set(expected_cookies))

    def _assert_consistent_expires(self, response):
        """ Verify all cookies in the response have the same expiration. """
        self.assertEqual(1, len(set([response.cookies[c]['expires'] for c in response.cookies])))

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
        self._assert_consistent_expires(response)
        self._assert_recreate_jwt_from_cookies(response, can_recreate=False)

    @patch.dict("django.conf.settings.FEATURES", {"DISABLE_SET_JWT_COOKIES_FOR_TESTS": False})
    def test_set_logged_in_jwt_cookies(self):
        setup_login_oauth_client()
        self._set_use_jwt_cookie_header(self.request)
        response = cookies_api.set_logged_in_cookies(self.request, HttpResponse(), self.user)
        self._assert_cookies_present(response, cookies_api.ALL_LOGGED_IN_COOKIE_NAMES)
        self._assert_consistent_expires(response)
        self._assert_recreate_jwt_from_cookies(response, can_recreate=True)

    @ddt.data(*itertools.product([True, False], [True, False]))
    @ddt.unpack
    def test_delete_and_are_logged_in_cookies_set(self, jwt_cookies_disabled, jwk_is_set):
        jwt_private_signing_jwk = settings.JWT_AUTH['JWT_PRIVATE_SIGNING_JWK'] if jwk_is_set else None
        with patch.dict("django.conf.settings.FEATURES", {"DISABLE_SET_JWT_COOKIES_FOR_TESTS": jwt_cookies_disabled}):
            with patch.dict("django.conf.settings.JWT_AUTH", {"JWT_PRIVATE_SIGNING_JWK": jwt_private_signing_jwk}):
                setup_login_oauth_client()
                response = cookies_api.set_logged_in_cookies(self.request, HttpResponse(), self.user)
                self._copy_cookies_to_request(response, self.request)
                self.assertTrue(cookies_api.are_logged_in_cookies_set(self.request))

                cookies_api.delete_logged_in_cookies(response)
                self._copy_cookies_to_request(response, self.request)
                self.assertFalse(cookies_api.are_logged_in_cookies_set(self.request))

    @patch.dict("django.conf.settings.FEATURES", {"DISABLE_SET_JWT_COOKIES_FOR_TESTS": False})
    def test_refresh_jwt_cookies(self):
        def _get_refresh_token_value(response):
            return response.cookies[cookies_api.jwt_cookies.jwt_refresh_cookie_name()].value

        setup_login_oauth_client()
        self._set_use_jwt_cookie_header(self.request)
        response = cookies_api.set_logged_in_cookies(self.request, HttpResponse(), self.user)
        self._copy_cookies_to_request(response, self.request)

        new_response = cookies_api.refresh_jwt_cookies(self.request, HttpResponse())
        self._assert_recreate_jwt_from_cookies(new_response, can_recreate=True)
        self.assertNotEqual(
            _get_refresh_token_value(response),
            _get_refresh_token_value(new_response),
        )
