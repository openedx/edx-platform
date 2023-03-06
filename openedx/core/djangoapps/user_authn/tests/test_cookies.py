# pylint: disable=missing-docstring


from datetime import date
import json
from unittest.mock import MagicMock, patch
from django.conf import settings
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse
from edx_rest_framework_extensions.auth.jwt.decoder import jwt_decode_handler
from edx_rest_framework_extensions.auth.jwt.middleware import JwtAuthCookieMiddleware

from openedx.core.djangoapps.user_api.accounts.utils import retrieve_last_sitewide_block_completed
from openedx.core.djangoapps.user_authn import cookies as cookies_api
from openedx.core.djangoapps.user_authn.tests.utils import setup_login_oauth_client
from openedx.core.djangolib.testing.utils import skip_unless_lms
from common.djangoapps.student.tests.factories import AnonymousUserFactory, UserFactory, UserProfileFactory
from openedx.core.djangoapps.profile_images.tests.helpers import make_image_file
from openedx.core.djangoapps.profile_images.images import create_profile_images
from openedx.core.djangoapps.user_api.accounts.image_helpers import get_profile_image_names


class CookieTests(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.user.profile = UserProfileFactory.create(user=self.user)
        self.request = RequestFactory().get('/')
        self.request.user = self.user
        self.request.session = self._get_stub_session()

    def _get_stub_session(self, max_age=604800):
        return MagicMock(
            get_expiry_age=lambda: max_age,
        )

    def _convert_to_absolute_uris(self, request, urls_obj):
        """ Convert relative URL paths to absolute URIs """
        for url_name, url_path in urls_obj.items():
            urls_obj[url_name] = request.build_absolute_uri(url_path)

        return urls_obj

    def _get_expected_image_urls(self):
        expected_image_urls = {
            'full': '/static/default_500.png',
            'large': '/static/default_120.png',
            'medium': '/static/default_50.png',
            'small': '/static/default_30.png'
        }

        expected_image_urls = self._convert_to_absolute_uris(self.request, expected_image_urls)

        return expected_image_urls

    def _get_expected_header_urls(self):
        expected_header_urls = {
            'logout': reverse('logout'),
            'account_settings': reverse('account_settings'),
            'learner_profile': reverse('learner_profile', kwargs={'username': self.user.username}),
        }
        block_url = retrieve_last_sitewide_block_completed(self.user)
        if block_url:
            expected_header_urls['resume_block'] = block_url

        expected_header_urls = self._convert_to_absolute_uris(self.request, expected_header_urls)

        return expected_header_urls

    def _copy_cookies_to_request(self, response, request):
        request.COOKIES = {
            key: val.value
            for key, val in response.cookies.items()
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
        assert (cookies_api.jwt_cookies.jwt_cookie_name() in self.request.COOKIES) == can_recreate
        if can_recreate:
            jwt_string = self.request.COOKIES[cookies_api.jwt_cookies.jwt_cookie_name()]
            jwt = jwt_decode_handler(jwt_string)
            assert jwt['scopes'] == ['user_id', 'email', 'profile']

    def _assert_cookies_present(self, response, expected_cookies):
        """ Verify all expected_cookies are present in the response. """
        self.assertSetEqual(set(response.cookies.keys()), set(expected_cookies))

    def _assert_consistent_expires(self, response, num_of_unique_expires=1):
        """ Verify cookies in the response have the same expiration, as expected. """
        assert num_of_unique_expires == len({response.cookies[c]['expires'] for c in response.cookies})

    @skip_unless_lms
    def test_get_user_info_cookie_data(self):
        with make_image_file() as image_file:
            create_profile_images(image_file, get_profile_image_names(self.user.username))
            self.user.profile.profile_image_uploaded_at = date.today()
            self.user.profile.save()

        actual = cookies_api._get_user_info_cookie_data(self.request, self.user)  # pylint: disable=protected-access

        expected = {
            'version': settings.EDXMKTG_USER_INFO_COOKIE_VERSION,
            'username': self.user.username,
            'email': self.user.email,
            'header_urls': self._get_expected_header_urls(),
            'user_image_urls': self._get_expected_image_urls(),
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
        assert cookies_api.are_logged_in_cookies_set(self.request)

        cookies_api.delete_logged_in_cookies(response)
        self._copy_cookies_to_request(response, self.request)
        assert not cookies_api.are_logged_in_cookies_set(self.request)

    @patch.dict("django.conf.settings.FEATURES", {"DISABLE_SET_JWT_COOKIES_FOR_TESTS": False})
    def test_refresh_jwt_cookies(self):
        setup_login_oauth_client()
        self._set_use_jwt_cookie_header(self.request)
        response = cookies_api.get_response_with_refreshed_jwt_cookies(self.request, self.user)
        data = json.loads(response.content.decode('utf8').replace("'", '"'))
        assert data['success'] is True
        assert data['user_id'] == self.user.id
        assert data['expires_epoch_seconds'] > 0
        assert data['expires'] != 'not-found'
        self._assert_cookies_present(response, cookies_api.JWT_COOKIE_NAMES)
        self._assert_consistent_expires(response, num_of_unique_expires=1)
        self._assert_recreate_jwt_from_cookies(response, can_recreate=True)
