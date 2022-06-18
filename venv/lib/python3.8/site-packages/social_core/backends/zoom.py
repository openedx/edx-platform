import base64

from .oauth import BaseOAuth2


class ZoomOAuth2(BaseOAuth2):
    """
    Zoom OAuth2 authentication backend
    Doc Reference: https://marketplace.zoom.us/docs/guides/auth/oauth
    """
    name = 'zoom-oauth2'
    AUTHORIZATION_URL = 'https://zoom.us/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://zoom.us/oauth/token'
    USER_DETAILS_URL = 'https://api.zoom.us/v2/users/me'
    DEFAULT_SCOPE = ['user:read']
    ACCESS_TOKEN_METHOD = 'POST'
    REFRESH_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False
    EXTRA_DATA = [
        ('expires_in', 'expires')
    ]

    def user_data(self, access_token, *args, **kwargs):
        response = self.get_json(
            self.USER_DETAILS_URL, headers={
                'Authorization': 'Bearer {access_token}'.format(
                    access_token=access_token
                )
            }
        )
        return response

    def get_user_details(self, response):
        username = response.get('id', '')
        first_name = response.get('first_name', '')
        last_name = response.get('last_name', '')
        email = response.get('email', '')
        fullname = ''
        return {
            'username': username,
            'email': email,
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name,
        }

    def auth_complete_params(self, state=None):
        return {
            'grant_type': 'authorization_code',  # request auth code
            'code': self.data.get('code', ''),  # server response code
            'redirect_uri': self.get_redirect_uri(state),
        }

    def auth_headers(self):
        return {
            'Authorization': b'Basic ' + base64.urlsafe_b64encode(
                '{}:{}'.format(*self.get_key_and_secret()).encode()
            )
        }

    def refresh_token_params(self, token, *args, **kwargs):
        return {'refresh_token': token, 'grant_type': 'refresh_token'}
