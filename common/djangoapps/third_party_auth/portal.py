from requests import HTTPError

from django.conf import settings

from social.backends.oauth import BaseOAuth2
from social.exceptions import AuthCanceled

def get_primary_email(emails):
    for email in emails:
        if email['primary'] is True:
            return email['email']
    return None


class PortalOAuth2(BaseOAuth2):
    """Portal OAuth2 authentication backend"""
    auth_settings = settings.IONISX_AUTH

    name = 'portal-oauth2'
    ID_KEY = '_id'
    AUTHORIZATION_URL = auth_settings.get('AUTHORIZATION_URL')
    ACCESS_TOKEN_URL = auth_settings.get('ACCESS_TOKEN_URL')
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False

    USER_DATA_URL = auth_settings.get('USER_DATA_URL')

    def get_user_details(self, response):
        """Return user details from IONISx account"""
        return {
            'username': response['username'],
            'email': get_primary_email(response['emails']),
            'fullname': response['name']
        }

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json(
            self.USER_DATA_URL,
            headers={'Authorization': 'Bearer {0}'.format(access_token)}
        )

    def process_error(self, data):
        super(PortalOAuth2, self).process_error(data)
        if data.get('error_code'):
            raise AuthCanceled(self, data.get('error_message') or
                                     data.get('error_code'))
