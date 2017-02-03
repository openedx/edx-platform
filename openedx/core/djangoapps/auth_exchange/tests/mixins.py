"""
Mixins to facilitate testing OAuth connections to Django-OAuth-Toolkit or
Django-OAuth2-Provider.
"""

# pylint: disable=protected-access

from unittest import skip, expectedFailure
from django.test.client import RequestFactory

from openedx.core.djangoapps.oauth_dispatch import adapters
from openedx.core.djangoapps.oauth_dispatch.tests.constants import DUMMY_REDIRECT_URL

from ..views import DOTAccessTokenExchangeView


class DOPAdapterMixin(object):
    """
    Mixin to rewire existing tests to use django-oauth2-provider (DOP) backend

    Overwrites self.client_id, self.access_token, self.oauth2_adapter
    """
    client_id = 'dop_test_client_id'
    access_token = 'dop_test_access_token'
    oauth2_adapter = adapters.DOPAdapter()

    def create_public_client(self, user, client_id=None):
        """
        Create an oauth client application that is public.
        """
        return self.oauth2_adapter.create_public_client(
            name='Test Public Client',
            user=user,
            client_id=client_id,
            redirect_uri=DUMMY_REDIRECT_URL,
        )

    def create_confidential_client(self, user, client_id=None):
        """
        Create an oauth client application that is confidential.
        """
        return self.oauth2_adapter.create_confidential_client(
            name='Test Confidential Client',
            user=user,
            client_id=client_id,
            redirect_uri=DUMMY_REDIRECT_URL,
        )

    def get_token_response_keys(self):
        """
        Return the set of keys provided when requesting an access token
        """
        return {'access_token', 'token_type', 'expires_in', 'scope'}


class DOTAdapterMixin(object):
    """
    Mixin to rewire existing tests to use django-oauth-toolkit (DOT) backend

    Overwrites self.client_id, self.access_token, self.oauth2_adapter
    """

    client_id = 'dot_test_client_id'
    access_token = 'dot_test_access_token'
    oauth2_adapter = adapters.DOTAdapter()

    def create_public_client(self, user, client_id=None):
        """
        Create an oauth client application that is public.
        """
        return self.oauth2_adapter.create_public_client(
            name='Test Public Application',
            user=user,
            client_id=client_id,
            redirect_uri=DUMMY_REDIRECT_URL,
        )

    def create_confidential_client(self, user, client_id=None):
        """
        Create an oauth client application that is confidential.
        """
        return self.oauth2_adapter.create_confidential_client(
            name='Test Confidential Application',
            user=user,
            client_id=client_id,
            redirect_uri=DUMMY_REDIRECT_URL,
        )

    def get_token_response_keys(self):
        """
        Return the set of keys provided when requesting an access token
        """
        return {'access_token', 'refresh_token', 'token_type', 'expires_in', 'scope'}

    def test_get_method(self):
        # Dispatch routes all get methods to DOP, so we test this on the view
        request_factory = RequestFactory()
        request = request_factory.get('/oauth2/exchange_access_token/')
        request.session = {}
        view = DOTAccessTokenExchangeView.as_view()
        response = view(request, backend='facebook')
        self.assertEqual(response.status_code, 400)

    @expectedFailure
    def test_single_access_token(self):
        # TODO: Single access tokens not supported yet for DOT (See MA-2122)
        super(DOTAdapterMixin, self).test_single_access_token()

    @skip("Not supported yet (See MA-2123)")
    def test_scopes(self):
        super(DOTAdapterMixin, self).test_scopes()
