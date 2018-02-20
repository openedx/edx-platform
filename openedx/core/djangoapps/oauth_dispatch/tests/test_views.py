"""
Tests for Blocks Views
"""

import json

import ddt
from django.conf import settings
from django.test import RequestFactory, TestCase
from django.core.urlresolvers import reverse
import httpretty
from oauth2_provider import models as dot_models
from provider import constants
import unittest

from student.tests.factories import UserFactory
from third_party_auth.tests.utils import ThirdPartyOAuthTestMixin, ThirdPartyOAuthTestMixinGoogle

from .constants import DUMMY_REDIRECT_URL
from . import mixins
from .. import adapters
from .. import models

if settings.FEATURES.get("ENABLE_OAUTH2_PROVIDER"):
    from .. import views


class AccessTokenLoginMixin(object):
    """
    Shared helper class to assert proper access levels when using access_tokens
    """

    def setUp(self):
        """
        Initialize mixin
        """
        super(AccessTokenLoginMixin, self).setUp()
        self.login_with_access_token_url = reverse("login_with_access_token")

    def login_with_access_token(self, access_token=None):
        """
        Login with access token and return response.
        You can optionally send in an accss_token to override
        the object's attribute
        """

        return self.client.post(
            self.login_with_access_token_url,
            HTTP_AUTHORIZATION="Bearer {0}".format(access_token if access_token else self.access_token)
        )

    def _assert_access_token_is_valid(self, access_token=None):
        """
        Asserts that oauth assigned access_token is valid and usable
        """
        self.assertEqual(self.login_with_access_token(access_token=access_token).status_code, 204)

    def _assert_access_token_invalidated(self, access_token=None):
        """
        Asserts that oauth assigned access_token is not valid
        """
        self.assertEqual(self.login_with_access_token(access_token=access_token).status_code, 401)


@unittest.skipUnless(settings.FEATURES.get("ENABLE_OAUTH2_PROVIDER"), "OAuth2 not enabled")
class _DispatchingViewTestCase(TestCase):
    """
    Base class for tests that exercise DispatchingViews.

    Subclasses need to define self.url.
    """
    dop_adapter = adapters.DOPAdapter()
    dot_adapter = adapters.DOTAdapter()

    def setUp(self):
        super(_DispatchingViewTestCase, self).setUp()
        self.user = UserFactory()
        self.dot_app = self.dot_adapter.create_public_client(
            name='test dot application',
            user=self.user,
            redirect_uri=DUMMY_REDIRECT_URL,
            client_id='dot-app-client-id',
        )
        self.dop_app = self.dop_adapter.create_public_client(
            name='test dop client',
            user=self.user,
            redirect_uri=DUMMY_REDIRECT_URL,
            client_id='dop-app-client-id',
        )

        # Create a "restricted" DOT Application which means any AccessToken/JWT
        # generated for this application will be immediately expired
        self.restricted_dot_app = self.dot_adapter.create_public_client(
            name='test restricted dot application',
            user=self.user,
            redirect_uri=DUMMY_REDIRECT_URL,
            client_id='dot-restricted-app-client-id',
        )
        models.RestrictedApplication.objects.create(application=self.restricted_dot_app)

    def _post_request(self, user, client, token_type=None):
        """
        Call the view with a POST request objectwith the appropriate format,
        returning the response object.
        """
        return self.client.post(self.url, self._post_body(user, client, token_type))  # pylint: disable=no-member

    def _post_body(self, user, client, token_type=None):
        """
        Return a dictionary to be used as the body of the POST request
        """
        raise NotImplementedError()


@ddt.ddt
class TestAccessTokenView(AccessTokenLoginMixin, mixins.AccessTokenMixin, _DispatchingViewTestCase):
    """
    Test class for AccessTokenView
    """
    def setUp(self):
        super(TestAccessTokenView, self).setUp()
        self.url = reverse('access_token')
        self.view_class = views.AccessTokenView

    def _post_body(self, user, client, token_type=None):
        """
        Return a dictionary to be used as the body of the POST request
        """
        body = {
            'client_id': client.client_id,
            'grant_type': 'password',
            'username': user.username,
            'password': 'test',
        }

        if token_type:
            body['token_type'] = token_type

        return body

    @ddt.data('dop_app', 'dot_app')
    def test_access_token_fields(self, client_attr):
        client = getattr(self, client_attr)
        response = self._post_request(self.user, client)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('access_token', data)
        self.assertIn('expires_in', data)
        self.assertIn('scope', data)
        self.assertIn('token_type', data)

    def test_restricted_access_token_fields(self):
        response = self._post_request(self.user, self.restricted_dot_app)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('access_token', data)
        self.assertIn('expires_in', data)
        self.assertIn('scope', data)
        self.assertIn('token_type', data)

        # Restricted applications have immediately expired tokens
        self.assertLess(data['expires_in'], 0)

        # double check that the token stored in the DB is marked as expired
        access_token = dot_models.AccessToken.objects.get(token=data['access_token'])
        self.assertTrue(models.RestrictedApplication.verify_access_token_as_expired(access_token))

    @ddt.data('dop_app', 'dot_app')
    def test_jwt_access_token(self, client_attr):
        client = getattr(self, client_attr)
        response = self._post_request(self.user, client, token_type='jwt')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('expires_in', data)
        self.assertEqual(data['token_type'], 'JWT')
        self.assert_valid_jwt_access_token(data['access_token'], self.user, data['scope'].split(' '))

    def test_restricted_jwt_access_token(self):
        """
        Verify that when requesting a JWT token from a restricted Application
        within the DOT subsystem, that our claims is marked as already expired
        (i.e. expiry set to Jan 1, 1970)
        """
        response = self._post_request(self.user, self.restricted_dot_app, token_type='jwt')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('expires_in', data)

        # jwt must indicate that it is already expired
        self.assertLess(data['expires_in'], 0)
        self.assertEqual(data['token_type'], 'JWT')
        self.assert_valid_jwt_access_token(
            data['access_token'],
            self.user,
            data['scope'].split(' '),
            should_be_expired=True
        )

    def test_restricted_access_token(self):
        """
        Verify that an access_token generated for a RestrictedApplication fails when
        submitted to an API endpoint
        """

        response = self._post_request(self.user, self.restricted_dot_app)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertIn('expires_in', data)
        self.assertIn('access_token', data)

        # the payload should indicate that the token is expired
        self.assertLess(data['expires_in'], 0)

        # try submitting this expired access_token to an API,
        # and assert that it fails
        self._assert_access_token_invalidated(data['access_token'])

    def test_dot_access_token_provides_refresh_token(self):
        response = self._post_request(self.user, self.dot_app)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('refresh_token', data)

    def test_dop_public_client_access_token(self):
        response = self._post_request(self.user, self.dop_app)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertNotIn('refresh_token', data)


@ddt.ddt
@httpretty.activate
class TestAccessTokenExchangeView(ThirdPartyOAuthTestMixinGoogle, ThirdPartyOAuthTestMixin, _DispatchingViewTestCase):
    """
    Test class for AccessTokenExchangeView
    """
    def setUp(self):
        self.url = reverse('exchange_access_token', kwargs={'backend': 'google-oauth2'})
        self.view_class = views.AccessTokenExchangeView
        super(TestAccessTokenExchangeView, self).setUp()

    def _post_body(self, user, client, token_type=None):
        return {
            'client_id': client.client_id,
            'access_token': self.access_token,
        }

    @ddt.data('dop_app', 'dot_app')
    def test_access_token_exchange_calls_dispatched_view(self, client_attr):
        client = getattr(self, client_attr)
        self.oauth_client = client
        self._setup_provider_response(success=True)
        response = self._post_request(self.user, client)
        self.assertEqual(response.status_code, 200)


# pylint: disable=abstract-method
@ddt.ddt
class TestAuthorizationView(_DispatchingViewTestCase):
    """
    Test class for AuthorizationView
    """

    dop_adapter = adapters.DOPAdapter()

    def setUp(self):
        super(TestAuthorizationView, self).setUp()
        self.user = UserFactory()
        self.dot_app = self.dot_adapter.create_confidential_client(
            name='test dot application',
            user=self.user,
            redirect_uri=DUMMY_REDIRECT_URL,
            client_id='confidential-dot-app-client-id',
        )
        self.dop_app = self.dop_adapter.create_confidential_client(
            name='test dop client',
            user=self.user,
            redirect_uri=DUMMY_REDIRECT_URL,
            client_id='confidential-dop-app-client-id',
        )

    @ddt.data(
        ('dop', 'authorize'),
        ('dot', 'allow')
    )
    @ddt.unpack
    def test_post_authorization_view(self, client_type, allow_field):
        oauth_application = getattr(self, '{}_app'.format(client_type))
        self.client.login(username=self.user.username, password='test')
        response = self.client.post(
            '/oauth2/authorize/',
            {
                'client_id': oauth_application.client_id,
                'response_type': 'code',
                'state': 'random_state_string',
                'redirect_uri': DUMMY_REDIRECT_URL,
                'scope': 'profile email',
                allow_field: True,
            },
            follow=True,
        )

        check_response = getattr(self, '_check_{}_response'.format(client_type))
        check_response(response)

    def test_check_dot_authorization_page_get(self):
        """
        Make sure we get the overridden Authorization page - not
        the default django-oauth-toolkit when we perform a page load
        """
        self.client.login(username=self.user.username, password='test')
        response = self.client.get(
            '/oauth2/authorize/',
            {
                'client_id': self.dot_app.client_id,
                'response_type': 'code',
                'state': 'random_state_string',
                'redirect_uri': DUMMY_REDIRECT_URL,
                'scope': 'profile'
            },
            follow=True,
        )

        # are the requested scopes on the page? We only requested 'profile', lets make
        # sure the page only lists that one
        self.assertContains(response, settings.OAUTH2_PROVIDER['SCOPES']['profile'])
        self.assertNotContains(response, settings.OAUTH2_PROVIDER['SCOPES']['read'])
        self.assertNotContains(response, settings.OAUTH2_PROVIDER['SCOPES']['write'])
        self.assertNotContains(response, settings.OAUTH2_PROVIDER['SCOPES']['email'])

        # is the application name specified?
        self.assertContains(
            response,
            "Authorize {name}".format(name=self.dot_app.name)
        )

        # are the cancel and allow buttons on the page?
        self.assertContains(
            response,
            '<button type="submit" class="btn btn-authorization-cancel" name="cancel"/>Cancel</button>'
        )
        self.assertContains(
            response,
            '<button type="submit" class="btn btn-authorization-allow" name="allow" value="Authorize"/>Allow</button>'
        )

    def _check_dot_response(self, response):
        """
        Check that django-oauth-toolkit gives an appropriate authorization response.
        """
        # django-oauth-toolkit tries to redirect to the user's redirect URL
        self.assertEqual(response.status_code, 404)  # We used a non-existent redirect url.
        expected_redirect_prefix = u'{}?'.format(DUMMY_REDIRECT_URL)
        self._assert_startswith(self._redirect_destination(response), expected_redirect_prefix)

    def _check_dop_response(self, response):
        """
        Check that django-oauth2-provider gives an appropriate authorization response.
        """
        # django-oauth-provider redirects to a confirmation page
        self.assertRedirects(response, u'http://testserver/oauth2/authorize/confirm', target_status_code=200)

        context = response.context_data
        form = context['form']
        self.assertIsNone(form['authorize'].value())

        oauth_data = context['oauth_data']
        self.assertEqual(oauth_data['redirect_uri'], DUMMY_REDIRECT_URL)
        self.assertEqual(oauth_data['state'], 'random_state_string')
        # TODO: figure out why it chooses this scope.
        self.assertEqual(oauth_data['scope'], constants.READ_WRITE)

    def _assert_startswith(self, string, prefix):
        """
        Assert that the string starts with the specified prefix.
        """
        self.assertTrue(string.startswith(prefix), u'{} does not start with {}'.format(string, prefix))

    @staticmethod
    def _redirect_destination(response):
        """
        Return the final destination of the redirect chain in the response object
        """
        return response.redirect_chain[-1][0]


@unittest.skipUnless(settings.FEATURES.get("ENABLE_OAUTH2_PROVIDER"), "OAuth2 not enabled")
class TestViewDispatch(TestCase):
    """
    Test that the DispatchingView dispatches the right way.
    """

    dop_adapter = adapters.DOPAdapter()
    dot_adapter = adapters.DOTAdapter()

    def setUp(self):
        super(TestViewDispatch, self).setUp()
        self.user = UserFactory()
        self.view = views._DispatchingView()  # pylint: disable=protected-access
        self.dop_adapter.create_public_client(
            name='',
            user=self.user,
            client_id='dop-id',
            redirect_uri=DUMMY_REDIRECT_URL
        )
        self.dot_adapter.create_public_client(
            name='',
            user=self.user,
            client_id='dot-id',
            redirect_uri=DUMMY_REDIRECT_URL
        )

    def assert_is_view(self, view_candidate):
        """
        Assert that a given object is a view.  That is, it is callable, and
        takes a request argument.  Note: while technically, the request argument
        could take any name, this assertion requires the argument to be named
        `request`.  This is good practice.  You should do it anyway.
        """
        _msg_base = u'{view} is not a view: {reason}'
        msg_not_callable = _msg_base.format(view=view_candidate, reason=u'it is not callable')
        msg_no_request = _msg_base.format(view=view_candidate, reason=u'it has no request argument')
        self.assertTrue(hasattr(view_candidate, '__call__'), msg_not_callable)
        args = view_candidate.func_code.co_varnames
        self.assertTrue(args, msg_no_request)
        self.assertEqual(args[0], 'request')

    def _post_request(self, client_id):
        """
        Return a request with the specified client_id in the body
        """
        return RequestFactory().post('/', {'client_id': client_id})

    def _get_request(self, client_id):
        """
        Return a request with the specified client_id in the get parameters
        """
        return RequestFactory().get('/?client_id={}'.format(client_id))

    def test_dispatching_post_to_dot(self):
        request = self._post_request('dot-id')
        self.assertEqual(self.view.select_backend(request), self.dot_adapter.backend)

    def test_dispatching_post_to_dop(self):
        request = self._post_request('dop-id')
        self.assertEqual(self.view.select_backend(request), self.dop_adapter.backend)

    def test_dispatching_get_to_dot(self):
        request = self._get_request('dot-id')
        self.assertEqual(self.view.select_backend(request), self.dot_adapter.backend)

    def test_dispatching_get_to_dop(self):
        request = self._get_request('dop-id')
        self.assertEqual(self.view.select_backend(request), self.dop_adapter.backend)

    def test_dispatching_with_no_client(self):
        request = self._post_request(None)
        self.assertEqual(self.view.select_backend(request), self.dop_adapter.backend)

    def test_dispatching_with_invalid_client(self):
        request = self._post_request('abcesdfljh')
        self.assertEqual(self.view.select_backend(request), self.dop_adapter.backend)

    def test_get_view_for_dot(self):
        view_object = views.AccessTokenView()
        self.assert_is_view(view_object.get_view_for_backend(self.dot_adapter.backend))

    def test_get_view_for_dop(self):
        view_object = views.AccessTokenView()
        self.assert_is_view(view_object.get_view_for_backend(self.dop_adapter.backend))

    def test_get_view_for_no_backend(self):
        view_object = views.AccessTokenView()
        self.assertRaises(KeyError, view_object.get_view_for_backend, None)


class TestRevokeTokenView(AccessTokenLoginMixin, _DispatchingViewTestCase):  # pylint: disable=abstract-method
    """
    Test class for RevokeTokenView
    """
    def setUp(self):
        self.revoke_token_url = reverse('revoke_token')
        self.access_token_url = reverse('access_token')

        super(TestRevokeTokenView, self).setUp()
        response = self.client.post(self.access_token_url, self.access_token_post_body_with_password())
        access_token_data = json.loads(response.content)
        self.access_token = access_token_data['access_token']
        self.refresh_token = access_token_data['refresh_token']

    def access_token_post_body_with_password(self):
        """
        Returns a dictionary to be used as the body of the access_token
        POST request with 'password' grant
        """
        return {
            'client_id': self.dot_app.client_id,
            'grant_type': 'password',
            'username': self.user.username,
            'password': 'test',
        }

    def access_token_post_body_with_refresh_token(self, refresh_token):
        """
        Returns a dictionary to be used as the body of the access_token
        POST request with 'refresh_token' grant
        """
        return {
            'client_id': self.dot_app.client_id,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }

    def revoke_token_post_body(self, token):
        """
        Returns a dictionary to be used as the body of the revoke_token POST request
        """
        return {
            'client_id': self.dot_app.client_id,
            'token': token,
        }

    def _assert_refresh_token_invalidated(self):
        """
        Asserts that oauth assigned refresh_token is not valid
        """
        response = self.client.post(
            self.access_token_url,
            self.access_token_post_body_with_refresh_token(self.refresh_token)
        )
        self.assertEqual(response.status_code, 401)

    def verify_revoke_token(self, token):
        """
        Verifies access of token before and after revoking
        """
        self._assert_access_token_is_valid()

        response = self.client.post(self.revoke_token_url, self.revoke_token_post_body(token))
        self.assertEqual(response.status_code, 200)

        self._assert_access_token_invalidated()
        self._assert_refresh_token_invalidated()

    def test_revoke_refresh_token_dot(self):
        """
        Tests invalidation/revoke of user tokens against refresh token for django-oauth-toolkit
        """
        self.verify_revoke_token(self.refresh_token)

    def test_revoke_access_token_dot(self):
        """
        Tests invalidation/revoke of user access token for django-oauth-toolkit
        """
        self.verify_revoke_token(self.access_token)
