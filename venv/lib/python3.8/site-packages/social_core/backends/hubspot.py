"""
HubSpot OAuth2 backend, docs at:
    https://developers.hubspot.com/docs/methods/oauth2/oauth2-overview
"""
from .oauth import BaseOAuth2


class HubSpotOAuth2(BaseOAuth2):
    """HubSpot OAuth2 authentication backend"""
    name = 'hubspot'
    AUTHORIZATION_URL = 'https://app.hubspot.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://api.hubapi.com/oauth/v1/token'
    ACCESS_TOKEN_METHOD = 'POST'
    USER_DATA_URL = 'https://api.hubapi.com/oauth/v1/access-tokens/'
    DEFAULT_SCOPE = ['oauth']
    EXTRA_DATA = [
        ('hub_domain', 'hub_domain'),
        ('hub_id', 'hub_id'),
        ('app_id', 'app_id'),
        ('user_id', 'user_id'),
        ('refresh_token', 'refresh_token'),
        ('expires_in', 'expires')
    ]

    def get_user_details(self, response):
        """Return user details"""
        response['email'] = response['user']
        return response

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data information from service"""
        return self.get_json(self.USER_DATA_URL + access_token, headers={
          'Authorization': 'Bearer ' + access_token
        })
