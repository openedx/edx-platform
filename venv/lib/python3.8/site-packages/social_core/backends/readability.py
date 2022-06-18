"""
Readability OAuth1 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/readability.html
"""
from .oauth import BaseOAuth1

READABILITY_API = 'https://www.readability.com/api/rest/v1'


class ReadabilityOAuth(BaseOAuth1):
    """Readability OAuth authentication backend"""
    name = 'readability'
    ID_KEY = 'username'
    AUTHORIZATION_URL = f'{READABILITY_API}/oauth/authorize/'
    REQUEST_TOKEN_URL = f'{READABILITY_API}/oauth/request_token/'
    ACCESS_TOKEN_URL = f'{READABILITY_API}/oauth/access_token/'
    EXTRA_DATA = [('date_joined', 'date_joined'),
                  ('kindle_email_address', 'kindle_email_address'),
                  ('avatar_url', 'avatar_url'),
                  ('email_into_address', 'email_into_address')]

    def get_user_details(self, response):
        fullname, first_name, last_name = self.get_user_names(
            first_name=response['first_name'],
            last_name=response['last_name']
        )
        return {'username': response['username'],
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token):
        return self.get_json(READABILITY_API + '/users/_current',
                             auth=self.oauth_auth(access_token))
