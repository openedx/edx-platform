# pylint: disable=missing-docstring


import six
from django.conf import settings
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse
from edx_rest_framework_extensions.auth.jwt.decoder import jwt_decode_handler
from edx_rest_framework_extensions.auth.jwt.middleware import JwtAuthCookieMiddleware
from mock import MagicMock, patch

from openedx.core.djangoapps.user_api.accounts.utils import retrieve_last_sitewide_block_completed
from openedx.core.djangoapps.user_authn import cookies as cookies_api
from openedx.core.djangoapps.user_authn.tests.utils import setup_login_oauth_client
from openedx.core.djangolib.testing.utils import skip_unless_lms
from common.djangoapps.student.tests.factories import AnonymousUserFactory, UserFactory


class CookieTests(TestCase):
    def setUp(self):
        super(CookieTests, self).setUp()
        self.user = UserFactory.create()
        self.request = RequestFactory().get('/')
        self.request.user = self.user
        self.request.session = self._get_stub_session()

    def _get_stub_session(self, max_age=604800):
        return MagicMock(
            get_expiry_age=lambda: max_age,
        )

    def _get_expected_header_urls(self):
        expected_header_urls = {
            'logout': reverse('logout'),
            'resume_block': retrieve_last_sitewide_block_completed(self.user),
            'account_settings': reverse('account_settings'),
            'learner_profile': reverse('learner_profile', kwargs={'username': self.user.username}),
        }

        # Convert relative URL paths to absolute URIs
        for url_name, url_path in six.iteritems(expected_header_urls):
            expected_header_urls[url_name] = self.request.build_absolute_uri(url_path)

        return expected_header_urls

    def _copy_cookies_to_request(self, response, request):
        request.COOKIES = {
            key: val.value
            for key, val in six.iteritems(response.cookies)
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
        JwtAuthCookieMiddleware().process_view(self.request, None, None, None)
        self.assertEqual(
            cookies_api.jwt_cookies.jwt_cookie_name() in self.request.COOKIES,
            can_recreate,
        )
        if can_recreate:
            jwt_string = self.request.COOKIES[cookies_api.jwt_cookies.jwt_cookie_name()]
            jwt = jwt_decode_handler(jwt_string)
            self.assertEqual(jwt['scopes'], ['user_id', 'email', 'profile'])

    def _assert_cookies_present(self, response, expected_cookies):
        """ Verify all expected_cookies are present in the response. """
        self.assertSetEqual(set(response.cookies.keys()), set(expected_cookies))

    def _assert_consistent_expires(self, response, num_of_unique_expires=1):
        """ Verify cookies in the response have the same expiration, as expected. """
        self.assertEqual(
            num_of_unique_expires,
            len(set([response.cookies[c]['expires'] for c in response.cookies])),
        )

    @skip_unless_lms
    def test_get_user_info_cookie_data(self):
        actual = cookies_api._get_user_info_cookie_data(self.request, self.user)  # pylint: disable=protected-access

        expected = {
            'version': settings.EDXMKTG_USER_INFO_COOKIE_VERSION,
            'username': self.user.username,
            'header_urls': self._get_expected_header_urls(),
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
        self._assert_consistent_expires(response, num_of_unique_expires=2)
        self._assert_recreate_jwt_from_cookies(response, can_recreate=True)

    @patch.dict("django.conf.settings.FEATURES", {"DISABLE_SET_JWT_COOKIES_FOR_TESTS": False})
    def test_delete_and_are_logged_in_cookies_set(self):
        setup_login_oauth_client()
        response = cookies_api.set_logged_in_cookies(self.request, HttpResponse(), self.user)
        self._copy_cookies_to_request(response, self.request)
        self.assertTrue(cookies_api.are_logged_in_cookies_set(self.request))

        cookies_api.delete_logged_in_cookies(response)
        self._copy_cookies_to_request(response, self.request)
        self.assertFalse(cookies_api.are_logged_in_cookies_set(self.request))

    @patch.dict("django.conf.settings.FEATURES", {"DISABLE_SET_JWT_COOKIES_FOR_TESTS": False})
    def test_refresh_jwt_cookies(self):
        setup_login_oauth_client()
        self._set_use_jwt_cookie_header(self.request)
        response = cookies_api.refresh_jwt_cookies(self.request, HttpResponse(), self.user)
        self._assert_cookies_present(response, cookies_api.JWT_COOKIE_NAMES)
        self._assert_consistent_expires(response, num_of_unique_expires=1)
        self._assert_recreate_jwt_from_cookies(response, can_recreate=True)
