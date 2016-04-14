"""
Tests for Blocks Views
"""

import json

import ddt
from django.test import RequestFactory, TestCase
from django.core.urlresolvers import reverse
import httpretty

from student.tests.factories import UserFactory
from third_party_auth.tests.utils import ThirdPartyOAuthTestMixin, ThirdPartyOAuthTestMixinGoogle

from .. import adapters
from .. import views
from .constants import DUMMY_REDIRECT_URL


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
        self.dop_client = self.dop_adapter.create_public_client(
            name='test dop client',
            user=self.user,
            redirect_uri=DUMMY_REDIRECT_URL,
            client_id='dop-app-client-id',
        )

    def _post_request(self, user, client):
        """
        Call the view with a POST request objectwith the appropriate format,
        returning the response object.
        """
        return self.client.post(self.url, self._post_body(user, client))

    def _post_body(self, user, client):
        """
        Return a dictionary to be used as the body of the POST request
        """
        raise NotImplementedError()


@ddt.ddt
class TestAccessTokenView(_DispatchingViewTestCase):
    """
    Test class for AccessTokenView
    """

    view_class = views.AccessTokenView
    url = reverse('access_token')

    def _post_body(self, user, client):
        """
        Return a dictionary to be used as the body of the POST request
        """
        return {
            'client_id': client.client_id,
            'grant_type': 'password',
            'username': user.username,
            'password': 'test',
        }

    @ddt.data('dop_client', 'dot_app')
    def test_access_token_fields(self, client_attr):
        client = getattr(self, client_attr)
        response = self._post_request(self.user, client)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('access_token', data)
        self.assertIn('expires_in', data)
        self.assertIn('scope', data)
        self.assertIn('token_type', data)

    def test_dot_access_token_provides_refresh_token(self):
        response = self._post_request(self.user, self.dot_app)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('refresh_token', data)

    def test_dop_public_client_access_token(self):
        response = self._post_request(self.user, self.dop_client)
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

    def _post_body(self, user, client):
        return {
            'client_id': client.client_id,
            'access_token': self.access_token,
        }

    @ddt.data('dop_client', 'dot_app')
    def test_access_token_exchange_calls_dispatched_view(self, client_attr):
        client = getattr(self, client_attr)
        self.oauth_client = client
        self._setup_provider_response(success=True)
        response = self._post_request(self.user, client)
        self.assertEqual(response.status_code, 200)


@ddt.ddt
class TestAuthorizationView(TestCase):
    """
    Test class for AuthorizationView
    """

    dop_adapter = adapters.DOPAdapter()

    def setUp(self):
        super(TestAuthorizationView, self).setUp()
        self.user = UserFactory()
        self.dop_client = self._create_confidential_client(user=self.user, client_id='dop-app-client-id')

    def _create_confidential_client(self, user, client_id):
        """
        Create a confidential client suitable for testing purposes.
        """
        return self.dop_adapter.create_confidential_client(
            name='test_app',
            user=user,
            client_id=client_id,
            redirect_uri=DUMMY_REDIRECT_URL
        )

    def test_authorization_view(self):
        self.client.login(username=self.user.username, password='test')
        response = self.client.post(
            '/oauth2/authorize/',
            {
                'client_id': self.dop_client.client_id,  # TODO: DOT is not yet supported (MA-2124)
                'response_type': 'code',
                'state': 'random_state_string',
                'redirect_uri': DUMMY_REDIRECT_URL,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        # check form is in context and form params are valid
        context = response.context_data  # pylint: disable=no-member
        self.assertIn('form', context)
        self.assertIsNone(context['form']['authorize'].value())

        self.assertIn('oauth_data', context)
        oauth_data = context['oauth_data']
        self.assertEqual(oauth_data['redirect_uri'], DUMMY_REDIRECT_URL)
        self.assertEqual(oauth_data['state'], 'random_state_string')


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

    def _get_request(self, client_id):
        """
        Return a request with the specified client_id in the body
        """
        return RequestFactory().post('/', {'client_id': client_id})

    def test_dispatching_to_dot(self):
        request = self._get_request('dot-id')
        self.assertEqual(self.view.select_backend(request), self.dot_adapter.backend)

    def test_dispatching_to_dop(self):
        request = self._get_request('dop-id')
        self.assertEqual(self.view.select_backend(request), self.dop_adapter.backend)

    def test_dispatching_with_no_client(self):
        request = self._get_request(None)
        self.assertEqual(self.view.select_backend(request), self.dop_adapter.backend)

    def test_dispatching_with_invalid_client(self):
        request = self._get_request('abcesdfljh')
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
