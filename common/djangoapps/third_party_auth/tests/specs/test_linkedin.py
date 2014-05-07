"""Integration tests for LinkedIn providers."""

from third_party_auth import provider
from third_party_auth.tests.specs import base


class LinkedInOauth2IntegrationTest(base.Oauth2IntegrationTest):
    """Integration tests for provider.LinkedInOauth2."""

    PROVIDER_CLASS = provider.LinkedInOauth2
    PROVIDER_SETTINGS = {
        'SOCIAL_AUTH_LINKEDIN_OAUTH2_KEY': 'linkedin_oauth2_key',
        'SOCIAL_AUTH_LINKEDIN_OAUTH2_SECRET': 'linkedin_oauth2_secret',
    }
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
