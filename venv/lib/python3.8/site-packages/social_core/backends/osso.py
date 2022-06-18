from urllib.parse import urlencode

from .oauth import BaseOAuth2


class OssoOAuth2(BaseOAuth2):
    """Osso OAuth authentication backend"""
    name = 'osso'
    REDIRECT_STATE = False
    STATE_PARAMETER = True
    AUTHORIZATION_URL = '{osso_base_url}/oauth/authorize'
    ACCESS_TOKEN_URL = '{osso_base_url}/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'

    @property
    def osso_base_url(self):
        return self.setting('OSSO_BASE_URL', 'https://demo.ossoapp.com')

    def authorization_url(self):
        return self.AUTHORIZATION_URL.format(osso_base_url=self.osso_base_url)

    def access_token_url(self):
        return self.ACCESS_TOKEN_URL.format(osso_base_url=self.osso_base_url)

    def auth_params(self, state=None):
        client_id, _client_secret = self.get_key_and_secret()
        params = {
            'client_id': client_id,
            'redirect_uri': self.get_redirect_uri(state)
        }
        if self.data.get('email'):
            params['email'] = self.data.get('email')
        if self.data.get('domain') and not self.data.get('email'):
            params['domain'] = self.data.get('domain')
        if self.STATE_PARAMETER and state:
            params['state'] = state
        if self.RESPONSE_TYPE:
            params['response_type'] = self.RESPONSE_TYPE
        return params


    def get_user_details(self, response):
        """Return user details from Osso"""
        return {'username': response.get('email'),
                'email': response.get('email')}

    def user_data(self, access_token, *args, **kwargs):
        """Loads normalized user profile from Osso"""
        url = f'{self.osso_base_url}/oauth/me?' + urlencode({
            'access_token': access_token
        })
        return self.get_json(url)