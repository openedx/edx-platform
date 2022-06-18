"""
Mail.ru OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/mailru.html
"""
from hashlib import md5
from urllib.parse import unquote

from .oauth import BaseOAuth2


class MailruOAuth2(BaseOAuth2):
    """Mail.ru authentication backend"""
    name = 'mailru-oauth2'
    ID_KEY = 'uid'
    AUTHORIZATION_URL = 'https://connect.mail.ru/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://connect.mail.ru/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'
    EXTRA_DATA = [('refresh_token', 'refresh_token'),
                  ('expires_in', 'expires')]

    def get_user_details(self, response):
        """Return user details from Mail.ru request"""
        fullname, first_name, last_name = self.get_user_names(
            first_name=unquote(response['first_name']),
            last_name=unquote(response['last_name'])
        )
        return {'username': unquote(response['nick']),
                'email': unquote(response['email']),
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        """Return user data from Mail.ru REST API"""
        key, secret = self.get_key_and_secret()
        data = {'method': 'users.getInfo',
                'session_key': access_token,
                'app_id': key,
                'secure': '1'}
        param_list = sorted(list(item + '=' + data[item] for item in data))
        data['sig'] = md5(
            (''.join(param_list) + secret).encode('utf-8')
        ).hexdigest()
        return self.get_json('http://www.appsmail.ru/platform/api',
                             params=data)[0]


class MRGOAuth2(BaseOAuth2):

    name = 'mailru'
    ID_KEY = 'email'
    AUTHORIZATION_URL = 'https://oauth.mail.ru/login'
    ACCESS_TOKEN_URL = 'https://oauth.mail.ru/token'
    ACCESS_TOKEN_METHOD = 'POST'
    EXTRA_DATA = [('refresh_token', 'refresh_token'),
                  ('expires_in', 'expires')]
    REDIRECT_STATE = False

    def get_user_details(self, response):
        return {
            'gender': response.get('gender'),
            'fullname': response.get('name'),
            'username': response.get('name'),
            'first_name': response.get('first_name'),
            'last_name': response.get('last_name'),
            'locale': response.get('locale'),
            'email': response.get('email'),
            'address': response.get('address'),
            'birthday': response.get('birthday'),
            'image': response.get('image'),
        }

    def user_data(self, access_token, *args, **kwargs):
        return self.get_json('https://oauth.mail.ru/userinfo', params={'access_token': access_token})
