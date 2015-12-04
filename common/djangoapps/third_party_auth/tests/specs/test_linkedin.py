"""Integration tests for LinkedIn providers."""

from third_party_auth.tests.specs import base


class LinkedInOauth2IntegrationTest(base.Oauth2IntegrationTest):
    """Integration tests for provider.LinkedInOauth2."""

    def setUp(self):
        super(LinkedInOauth2IntegrationTest, self).setUp()
        self.provider = self.configure_linkedin_provider(
            enabled=True,
            key='linkedin_oauth2_key',
            secret='linkedin_oauth2_secret',
        )

    TOKEN_RESPONSE_DATA = {
        'access_token': 'access_token_value',
        'expires_in': 'expires_in_value',
    }
    USER_RESPONSE_DATA = {
        'lastName': 'lastName_value',
        'id': 'id_value',
        'firstName': 'firstName_value',
    }

    def get_username(self):
        response_data = self.get_response_data()
        return response_data.get('firstName') + response_data.get('lastName')
