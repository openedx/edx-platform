"""Integration tests for Google providers."""

from third_party_auth import provider
from third_party_auth.tests.specs import base


class GoogleOauth2IntegrationTest(base.Oauth2IntegrationTest):
    """Integration tests for provider.GoogleOauth2."""

    def setUp(self):
        super(GoogleOauth2IntegrationTest, self).setUp()
        self.provider = self.configure_google_provider(
            enabled=True,
            key='google_oauth2_key',
            secret='google_oauth2_secret',
        )

    TOKEN_RESPONSE_DATA = {
        'access_token': 'access_token_value',
        'expires_in': 'expires_in_value',
        'id_token': 'id_token_value',
        'token_type': 'token_type_value',
    }
    USER_RESPONSE_DATA = {
        'email': 'email_value@example.com',
        'family_name': 'family_name_value',
        'given_name': 'given_name_value',
        'id': 'id_value',
        'link': 'link_value',
        'locale': 'locale_value',
        'name': 'name_value',
        'picture': 'picture_value',
        'verified_email': 'verified_email_value',
    }

    def get_username(self):
        return self.get_response_data().get('email').split('@')[0]
