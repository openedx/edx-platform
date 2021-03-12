"""
Mixins to facilitate testing OAuth connections to Django-OAuth-Toolkit or
Django-OAuth2-Provider.
"""
from openedx.core.djangoapps.oauth_dispatch import adapters
from openedx.core.djangoapps.oauth_dispatch.tests.constants import DUMMY_REDIRECT_URL


class DOTAdapterMixin:
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
