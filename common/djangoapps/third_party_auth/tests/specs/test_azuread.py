"""Integration tests for Azure Active Directory / Microsoft Account provider."""

from third_party_auth.tests.specs import base


# pylint: disable=test-inherits-tests
class AzureADOauth2IntegrationTest(base.Oauth2IntegrationTest):
    """Integration tests for Azure Active Directory / Microsoft Account provider."""

    def setUp(self):
        super(AzureADOauth2IntegrationTest, self).setUp()
        self.provider = self.configure_azure_ad_provider(
            enabled=True,
            visible=True,
            key='azure_ad_oauth2_key',
            secret='azure_ad_oauth2_secret',
        )

    TOKEN_RESPONSE_DATA = {
        'exp': 1234590302,
        'nbf': 1234586402,
        'iat': 1234586402,
        'expires_on': '1234590302',
        'ver': '1.0',
        'access_token': 'access_token_value',
        'expires_in': '3599',
        'id_token': 'id_token_value',
        'token_type': 'Bearer',
        'refresh_token': 'REFRESH1234567890',
        'iss': 'https://sts.windows.net/abcdefgh-1234-5678-900a-0aa0a00aa0aa/',
        'ipaddr': '123.123.123.123',
    }
    USER_RESPONSE_DATA = {
        'oid': 'abcdefgh-1234-5678-900a-0aa0a00aa0aa',
        'aud': 'abcdefgh-1234-5678-900a-0aa0a00aa0aa',
        'tid': 'abcdefgh-1234-5678-900a-0aa0a00aa0aa',
        'amr': ['pwd'],
        'unique_name': 'email_value@example.com',
        'upn': 'email_value@example.com',
        'family_name': 'family_name_value',
        'name': 'name_value',
        'given_name': 'given_name_value',
        'sub': 'aBC_ab12345678h94CSgP1lTYJCHATGQDAcfg8jSOck',
    }

    def get_username(self):
        return self.get_response_data().get('name')
