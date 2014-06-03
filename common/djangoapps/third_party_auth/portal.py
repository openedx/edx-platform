from requests import HTTPError

from django.conf import settings

from social.backends.oauth import BaseOAuth2
from social.exceptions import AuthCanceled


class PortalOAuth2(BaseOAuth2):
    """Portal OAuth2 authentication backend"""
    name = 'portal-oauth2'
    auth_settings = settings.IONISX_AUTH
    AUTHORIZATION_URL = auth_settings['AUTHORIZATION_URL']
    ACCESS_TOKEN_URL = auth_settings['ACCESS_TOKEN_URL']
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False
    USER_DATA_URL = auth_settings['USER_DATA_URL']

    def get_user_id(self, details, response):
        """Use portal email as unique id"""
        if self.setting('USE_UNIQUE_USER_ID', False):
            return response['id']
        else:
            return details['email']

    def get_user_details(self, response):
        """Return user details from Portal account"""
        return {'username': response.get('username', ''),
                'email': response.get('emails', '')[0]['email'],
                'fullname': response.get('name')}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        params = self.setting('PROFILE_EXTRA_PARAMS', {})
        params['access_token'] = access_token
        return self.get_json(self.USER_DATA_URL, params=params)

    def process_error(self, data):
        super(PortalOAuth2, self).process_error(data)
        if data.get('error_code'):
            raise AuthCanceled(self, data.get('error_message') or
                                     data.get('error_code'))
