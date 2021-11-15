# pylint: disable=missing-docstring


import ddt
from django.conf import settings
from django.http import QueryDict
from django.test import RequestFactory, TestCase
from unittest.mock import Mock, patch
from urllib.parse import urlparse

from common.djangoapps.student.tests.factories import AnonymousUserFactory, UserFactory
from openedx.core.djangoapps.user_authn.middleware import RedirectUnauthenticatedToLoginMiddleware


@ddt.ddt
@patch.dict("django.conf.settings.FEATURES", {"ENABLE_REDIRECT_UNAUTHENTICATED_USERS_TO_LOGIN": True})
class RedirectUnauthenticatedToLoginMiddlewareTests(TestCase):
    """
    Tests for RedirectUnauthenticatedToLoginMiddleware.
    """

    def setUp(self):
        super().setUp()
        self.mock_response = Mock()
        self.middleware = RedirectUnauthenticatedToLoginMiddleware(
            lambda request: self.mock_response
        )

    @ddt.data(
        RequestFactory().head('/'),
        RequestFactory().post('/'),
        RequestFactory().put('/'),
        RequestFactory().options('/'),
        RequestFactory().delete('/'),
    )
    def test_does_not_redirect_non_GET_requests(self, request):
        """
        Middleware doesn't redirect non GET requests.
        """
        request.user = AnonymousUserFactory.create()

        response = self.middleware(request)

        self.assertEqual(response, self.mock_response)

    def test_redirects_unauthenticated_user_to_login(self):
        """
        Middleware redirects unauthenticated user to login page.
        """
        request = RequestFactory().get('/')
        request.user = AnonymousUserFactory.create()

        response = self.middleware(request)

        self.assertNotEqual(response, self.mock_response)
        path = urlparse(response.url).path
        self.assertEqual(path, settings.LOGIN_URL)

    def test_passes_url_in_next_query_string(self):
        """
        Middleware passes url in 'next' query string parameter.

        When redirecting, the middleware should add 'next' query string
        parameter, that contains the url that was originally requested.
        """
        request = RequestFactory().get('/dashboard?test=123')
        request.user = AnonymousUserFactory.create()

        response = self.middleware(request)

        self.assertNotEqual(response, self.mock_response)
        query = QueryDict(urlparse(response.url).query)
        self.assertIn('next', query)
        self.assertEqual(query['next'], '/dashboard?test=123')

    def test_does_not_redirect_if_user_is_authenticated(self):
        """
        Middleware doesn't redirect authenticated users.
        """
        request = RequestFactory().get('/')
        request.user = UserFactory.create()

        response = self.middleware(request)

        self.assertEqual(response, self.mock_response)

    def test_get_login_does_not_redirect_unauthenticated_user(self):
        """
        Middleware doesn't redirect unauthenticated user visiting login page.
        """
        request = RequestFactory().get(settings.LOGIN_URL)
        request.user = AnonymousUserFactory.create()

        response = self.middleware(request)

        self.assertEqual(response, self.mock_response)

    def test_get_register_does_not_redirect_unauthenticated_user(self):
        """
        Middleware doesn't redirect unauthenticated user visiting register page.
        """
        request = RequestFactory().get('/register')
        request.user = AnonymousUserFactory.create()

        response = self.middleware(request)

        self.assertEqual(response, self.mock_response)

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_REDIRECT_UNAUTHENTICATED_USERS_TO_LOGIN": False})
    def test_does_not_redirect_unauthenticated_user_if_setting_disabled(self):
        """
        Middleware doesn't redirect if settings is set to False.

        If ENABLE_REDIRECT_UNAUTHENTICATED_USERS_TO_LOGIN setting is set to
        False, the middleware should not redirect unauthenticated users.
        """
        request = RequestFactory().get('/')
        request.user = AnonymousUserFactory.create()

        response = self.middleware(request)

        self.assertEqual(response, self.mock_response)
