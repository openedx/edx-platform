"""
Tests for Blocks Views
"""

import json

import ddt
from django.test import RequestFactory, TestCase
from django.core.urlresolvers import reverse
import httpretty
from provider import constants

from student.tests.factories import UserFactory
from third_party_auth.tests.utils import ThirdPartyOAuthTestMixin, ThirdPartyOAuthTestMixinGoogle

from .constants import DUMMY_REDIRECT_URL
from .. import adapters
from .. import views
from . import mixins


class _DispatchingViewTestCase(TestCase):
    """
    Base class for tests that exercise DispatchingViews.
    """
    dop_adapter = adapters.DOPAdapter()
    dot_adapter = adapters.DOTAdapter()

    view_class = None
    url = None

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

    def _post_request(self, user, client, token_type=None):
        """
        Call the view with a POST request objectwith the appropriate format,
        returning the response object.
        """
        return self.client.post(self.url, self._post_body(user, client, token_type))

    def _post_body(self, user, client, token_type=None):
        """
        Return a dictionary to be used as the body of the POST request
        """
        raise NotImplementedError()


@ddt.ddt
class TestAccessTokenView(mixins.AccessTokenMixin, _DispatchingViewTestCase):
    """
    Test class for AccessTokenView
    """

    view_class = views.AccessTokenView
    url = reverse('access_token')

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

    @ddt.data('dop_app', 'dot_app')
    def test_jwt_access_token(self, client_attr):
        client = getattr(self, client_attr)
        response = self._post_request(self.user, client, token_type='jwt')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('expires_in', data)
        self.assertEqual(data['token_type'], 'JWT')
        self.assert_valid_jwt_access_token(data['access_token'], self.user, data['scope'].split(' '))

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

    view_class = views.AccessTokenExchangeView
    url = reverse('exchange_access_token', kwargs={'backend': 'google-oauth2'})

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
