"""
Twitch OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/twitch.html
"""
from .oauth import BaseOAuth2
from .open_id_connect import OpenIdConnectAuth


class TwitchOpenIdConnect(OpenIdConnectAuth):
    """Twitch OpenID Connect authentication backend"""
    name = 'twitch'
    USERNAME_KEY = 'preferred_username'
    OIDC_ENDPOINT = 'https://id.twitch.tv/oauth2'
    DEFAULT_SCOPE = ['openid', 'user:read:email']
    TWITCH_CLAIMS = '{"id_token":{"email": null,"email_verified":null,"preferred_username":null}}'

    def auth_params(self, state=None):
        params = super().auth_params(state)
        # Twitch uses a non-compliant OpenID implementation where the claims must be passed as a param
        params['claims'] = self.TWITCH_CLAIMS
        return params

    def get_user_details(self, response):
        return {
            'username': self.id_token['preferred_username'],
            'email': self.id_token['email'],
            # Twitch does not provide this information
            'fullname': '',
            'first_name': '',
            'last_name': '',
        }


class TwitchOAuth2(BaseOAuth2):
    """Twitch OAuth authentication backend"""
    name = 'twitch'
    ID_KEY = '_id'
    AUTHORIZATION_URL = 'https://id.twitch.tv/oauth2/authorize'
    ACCESS_TOKEN_URL = 'https://id.twitch.tv/oauth2/token'
    ACCESS_TOKEN_METHOD = 'POST'
    DEFAULT_SCOPE = ['user:read:email']
    REDIRECT_STATE = False

    def get_user_id(self, details, response):
        """
        Use twitch user id as unique id
        """
        return response.get('id')

    def get_user_details(self, response):
        return {
            'username': response.get('login'),
            'email': response.get('email'),
            'first_name': '',
            'last_name': ''
        }

    def user_data(self, access_token, *args, **kwargs):
        client_id, _ = self.get_key_and_secret()
        auth_headers = {
            'Authorization': 'Bearer %s' % access_token,
            'Client-Id': client_id
        }
        url = 'https://api.twitch.tv/helix/users'

        data = self.get_json(url, headers=auth_headers)

        return data['data'][0] if data.get('data') else {}
