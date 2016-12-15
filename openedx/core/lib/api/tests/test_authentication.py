"""
Tests for OAuth2.  This module is copied from django-rest-framework-oauth
(tests/test_authentication.py) and updated to use our subclass of OAuth2Authentication.
"""

from __future__ import unicode_literals
from collections import namedtuple
from datetime import datetime, timedelta
import itertools
import json

import ddt
from django.conf.urls import patterns, url, include
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import TestCase
from django.utils import unittest
from django.utils.http import urlencode

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_oauth import permissions
from rest_framework_oauth.compat import oauth2_provider, oauth2_provider_scope
from rest_framework.test import APIRequestFactory, APIClient
from rest_framework.views import APIView

from provider import scope, constants
from openedx.core.lib.api import authentication


factory = APIRequestFactory()  # pylint: disable=invalid-name


class MockView(APIView):  # pylint: disable=missing-docstring
    permission_classes = (IsAuthenticated,)

    def get(self, request):  # pylint: disable=missing-docstring,unused-argument
        return HttpResponse({'a': 1, 'b': 2, 'c': 3})

    def post(self, request):  # pylint: disable=missing-docstring,unused-argument
        return HttpResponse({'a': 1, 'b': 2, 'c': 3})

    def put(self, request):  # pylint: disable=missing-docstring,unused-argument
        return HttpResponse({'a': 1, 'b': 2, 'c': 3})


# This is the a change we've made from the django-rest-framework-oauth version
# of these tests.  We're subclassing our custom OAuth2AuthenticationAllowInactiveUser
# instead of OAuth2Authentication.
class OAuth2AuthenticationDebug(authentication.OAuth2AuthenticationAllowInactiveUser):  # pylint: disable=missing-docstring
    allow_query_params_token = True


urlpatterns = patterns(
    '',
    url(r'^oauth2/', include('provider.oauth2.urls', namespace='oauth2')),
    url(
        r'^oauth2-test/$',
        MockView.as_view(authentication_classes=[authentication.OAuth2AuthenticationAllowInactiveUser])
    ),
    url(r'^oauth2-test-debug/$', MockView.as_view(authentication_classes=[OAuth2AuthenticationDebug])),
    url(
        r'^oauth2-with-scope-test/$',
        MockView.as_view(
            authentication_classes=[authentication.OAuth2AuthenticationAllowInactiveUser],
            permission_classes=[permissions.TokenHasReadWriteScope]
        )
    ),
)


@ddt.ddt
class OAuth2Tests(TestCase):
    """OAuth 2.0 authentication"""
    urls = 'openedx.core.lib.api.tests.test_authentication'

    def setUp(self):
        super(OAuth2Tests, self).setUp()
        self.csrf_client = APIClient(enforce_csrf_checks=True)
        self.username = 'john'
        self.email = 'lennon@thebeatles.com'
        self.password = 'password'
        self.user = User.objects.create_user(self.username, self.email, self.password)

        self.CLIENT_ID = 'client_key'  # pylint: disable=invalid-name
        self.CLIENT_SECRET = 'client_secret'  # pylint: disable=invalid-name
        self.ACCESS_TOKEN = 'access_token'  # pylint: disable=invalid-name
        self.REFRESH_TOKEN = 'refresh_token'  # pylint: disable=invalid-name

        self.oauth2_client = oauth2_provider.oauth2.models.Client.objects.create(
            client_id=self.CLIENT_ID,
            client_secret=self.CLIENT_SECRET,
            redirect_uri='',
            client_type=0,
            name='example',
            user=None,
        )

        self.access_token = oauth2_provider.oauth2.models.AccessToken.objects.create(
            token=self.ACCESS_TOKEN,
            client=self.oauth2_client,
            user=self.user,
        )
        self.refresh_token = oauth2_provider.oauth2.models.RefreshToken.objects.create(
            user=self.user,
            access_token=self.access_token,
            client=self.oauth2_client
        )

        # This is the a change we've made from the django-rest-framework-oauth version
        # of these tests.
        self.user.is_active = False
        self.user.save()

        # This is the a change we've made from the django-rest-framework-oauth version
        # of these tests.
        # Override the SCOPE_NAME_DICT setting for tests for oauth2-with-scope-test.  This is
        # needed to support READ and WRITE scopes as they currently aren't supported by the
        # edx-auth2-provider, and their scope values collide with other scopes defined in the
        # edx-auth2-provider.
        scope.SCOPE_NAME_DICT = {'read': constants.READ, 'write': constants.WRITE}

    def get_with_bearer_token(self, target_url, params=None, token=None):
        """
        Make a GET request to the specified URL with an OAuth2 bearer token.  If
        no token is provided, a valid token will be used.  Query parameters can
        also be passed in if desired.
        """
        auth = self._create_authorization_header(token)
        return self.csrf_client.get(target_url, params, HTTP_AUTHORIZATION=auth)

    def post_with_bearer_token(self, target_url, token=None):
        """
        Make a POST request to the specified URL with an OAuth2 bearer token.  If
        no token is provided, a valid token will be used.
        """
        auth = self._create_authorization_header(token)
        return self.csrf_client.post(target_url, HTTP_AUTHORIZATION=auth)

    def check_error_codes(self, response, status_code, error_code):
        """
        Ensure that the response has the appropriate HTTP status, and provides
        the expected error_code in the JSON response body.
        """
        response_dict = json.loads(response.content)
        self.assertEqual(response.status_code, status_code)
        self.assertEqual(response_dict['error_code'], error_code)

    def _create_authorization_header(self, token=None):  # pylint: disable=missing-docstring
        if token is None:
            token = self.access_token.token
        return "Bearer {0}".format(token)

    @ddt.data(None, {})
    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_get_form_with_wrong_authorization_header_token_type_failing(self, params):
        """Ensure that a wrong token type lead to the correct HTTP error status code"""
        response = self.csrf_client.get(
            '/oauth2-test/',
            params,
            HTTP_AUTHORIZATION='Wrong token-type-obviously'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # If no Authorization header is provided that contains a bearer token,
        # authorization passes to the next registered authorization class, or
        # (in this case) to standard DRF fallback code, so no error_code is
        # provided (yet).
        self.assertNotIn('error_code', json.loads(response.content))

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_get_form_passing_auth(self):
        """Ensure GETing form over OAuth with correct client credentials succeed"""
        response = self.get_with_bearer_token('/oauth2-test/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_post_form_passing_auth_url_transport(self):
        """Ensure GETing form over OAuth with correct client credentials in form data succeed"""
        response = self.csrf_client.post(
            '/oauth2-test/',
            data={'access_token': self.access_token.token}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_get_form_passing_auth_url_transport(self):
        """Ensure GETing form over OAuth with correct client credentials in query succeed when DEBUG is True"""
        query = urlencode({'access_token': self.access_token.token})
        response = self.csrf_client.get('/oauth2-test-debug/?%s' % query)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_get_form_failing_auth_url_transport(self):
        """Ensure GETing form over OAuth with correct client credentials in query fails when DEBUG is False"""
        query = urlencode({'access_token': self.access_token.token})
        response = self.csrf_client.get('/oauth2-test/?%s' % query)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # This case is handled directly by DRF so no error_code is provided (yet).
        self.assertNotIn('error_code', json.loads(response.content))

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_post_form_passing_auth(self):
        """Ensure POSTing form over OAuth with correct credentials passes and does not require CSRF"""
        response = self.post_with_bearer_token('/oauth2-test/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_post_form_token_removed_failing_auth(self):
        """Ensure POSTing when there is no OAuth access token in db fails"""
        self.access_token.delete()
        response = self.post_with_bearer_token('/oauth2-test/')
        self.check_error_codes(
            response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=authentication.OAUTH2_TOKEN_ERROR_NONEXISTENT
        )

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_post_form_with_refresh_token_failing_auth(self):
        """Ensure POSTing with refresh token instead of access token fails"""
        response = self.post_with_bearer_token('/oauth2-test/', token=self.refresh_token.token)
        self.check_error_codes(
            response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=authentication.OAUTH2_TOKEN_ERROR_NONEXISTENT
        )

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_post_form_with_expired_access_token_failing_auth(self):
        """Ensure POSTing with expired access token fails with a 'token_expired' error"""
        self.access_token.expires = datetime.now() - timedelta(seconds=10)  # 10 seconds late
        self.access_token.save()
        response = self.post_with_bearer_token('/oauth2-test/')
        self.check_error_codes(
            response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=authentication.OAUTH2_TOKEN_ERROR_EXPIRED
        )

    TokenErrorDDT = namedtuple('TokenErrorDDT', ['token', 'error_code'])

    @ddt.data(
        *itertools.product(
            [None, {}],
            [
                TokenErrorDDT('wrong format', authentication.OAUTH2_TOKEN_ERROR_MALFORMED),
                TokenErrorDDT('wrong-token', authentication.OAUTH2_TOKEN_ERROR_NONEXISTENT),
                TokenErrorDDT('', authentication.OAUTH2_TOKEN_ERROR_NOT_PROVIDED),
            ]
        )
    )
    @ddt.unpack
    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_response_for_get_request_with_bad_auth_token(self, http_params, token_error):
        response = self.get_with_bearer_token('/oauth2-test/', http_params, token=token_error.token)
        self.check_error_codes(
            response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=token_error.error_code
        )

    @ddt.data(
        TokenErrorDDT('notatoken', authentication.OAUTH2_TOKEN_ERROR_NONEXISTENT),
        TokenErrorDDT('malformed token', authentication.OAUTH2_TOKEN_ERROR_MALFORMED),
        TokenErrorDDT('', authentication.OAUTH2_TOKEN_ERROR_NOT_PROVIDED),
    )
    def test_response_for_post_request_with_bad_auth_token(self, token_error):
        response = self.post_with_bearer_token('/oauth2-test/', token=token_error.token)
        self.check_error_codes(response, status_code=status.HTTP_401_UNAUTHORIZED, error_code=token_error.error_code)

    ScopeStatusDDT = namedtuple('ScopeStatusDDT', ['scope', 'read_status', 'write_status'])

    @ddt.data(
        ScopeStatusDDT('read', read_status=status.HTTP_200_OK, write_status=status.HTTP_403_FORBIDDEN),
        ScopeStatusDDT('write', status.HTTP_403_FORBIDDEN, status.HTTP_200_OK),
    )
    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_responses_to_scoped_requests(self, scope_statuses):
        self.access_token.scope = oauth2_provider_scope.SCOPE_NAME_DICT[scope_statuses.scope]
        self.access_token.save()
        response = self.get_with_bearer_token('/oauth2-with-scope-test/', token=self.access_token.token)
        self.assertEqual(response.status_code, scope_statuses.read_status)
        response = self.post_with_bearer_token('/oauth2-with-scope-test/', token=self.access_token.token)
        self.assertEqual(response.status_code, scope_statuses.write_status)
