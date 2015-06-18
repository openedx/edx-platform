"""Integration tests for AzureAd providers."""

from third_party_auth import provider
from third_party_auth.tests.specs import base


class AzureADOAuth2IntegrationTest(base.Oauth2IntegrationTest):
    """Integration tests for provider.AzureADOAuth2."""

    PROVIDER_CLASS = provider.AzureADOauth2
    PROVIDER_SETTINGS = {
        'SOCIAL_AUTH_AZUREAD_OAUTH2_KEY': 'azure_oauth2_key',
        'SOCIAL_AUTH_AZUREAD_OAUTH2_SECRET': 'azure_oauth2_secret',
        'SOCIAL_AUTH_AZUREAD_OAUTH2_RESOURCE': 'https://mysite-my.sharepoint.com'
    }
    TOKEN_RESPONSE_DATA = {
        'access_token': 'foobar',
        'token_type': 'bearer',
        'id_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC83Mjc0MDZhYy03MDY4'
                    'LTQ4ZmEtOTJiOS1jMmQ2NzIxMWJjNTAvIiwiaWF0IjpudWxsLCJleHAiOm51bGwsImF1ZCI6IjAyOWNjMDEwLWJiNzQtNGQyY'
                    'i1hMDQwLWY5Y2VkM2ZkMmM3NiIsInN1YiI6InFVOHhrczltSHFuVjZRMzR6aDdTQVpvY2loOUV6cnJJOW1wVlhPSWJWQTgiLC'
                    'J2ZXIiOiIxLjAiLCJ0aWQiOiI3Mjc0MDZhYy03MDY4LTQ4ZmEtOTJiOS1jMmQ2NzIxMWJjNTAiLCJvaWQiOiI3ZjhlMTk2OS0'
                    '4YjgxLTQzOGMtOGQ0ZS1hZDZmNTYyYjI4YmIiLCJ1cG4iOiJmb29iYXJAdGVzdC5vbm1pY3Jvc29mdC5jb20iLCJnaXZlbl9u'
                    'YW1lIjoiZm9vIiwiZmFtaWx5X25hbWUiOiJiYXIiLCJuYW1lIjoiZm9vIGJhciIsInVuaXF1ZV9uYW1lIjoiZm9vYmFyQHRlc'
                    '3Qub25taWNyb3NvZnQuY29tIiwicHdkX2V4cCI6IjQ3MzMwOTY4IiwicHdkX3VybCI6Imh0dHBzOi8vcG9ydGFsLm1pY3Jvc2'
                    '9mdG9ubGluZS5jb20vQ2hhbmdlUGFzc3dvcmQuYXNweCJ9.3V50dHXTZOHj9UWtkn2g7BjX5JxNe8skYlK4PdhiLz4',
        'expires_in': 3600,
        'expires_on': 1423650396,
        'not_before': 1423646496
    }

    USER_RESPONSE_DATA = {
        "iss": "https://sts.windows.net/727406ac-7068-48fa-92b9-c2d67211bc50/",
        "iat": 'null',
        "exp": 'null',
        "aud": "029cc010-bb74-4d2b-a040-f9ced3fd2c76",
        "sub": "qU8xks9mHqnV6Q34zh7SAZocih9EzrrI9mpVXOIbVA8",
        "ver": "1.0",
        "tid": "727406ac-7068-48fa-92b9-c2d67211bc50",
        "oid": "7f8e1969-8b81-438c-8d4e-ad6f562b28bb",
        "upn": "foobar@test.onmicrosoft.com",
        "given_name": "foo",
        "family_name": "bar",
        "name": "foo bar",
        "unique_name": "foobar@test.onmicrosoft.com",
        "pwd_exp": "47330968",
        "pwd_url": "https://portal.microsoftonline.com/ChangePassword.aspx"
    }

    def get_username(self):
        response_data = self.get_response_data()
        return response_data.get('upn')

