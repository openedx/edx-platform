"""
Dropbox OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/dropbox.html
"""

from .oauth import BaseOAuth2


class DropboxOAuth2V2(BaseOAuth2):
    name = 'dropbox-oauth2'
    ID_KEY = 'uid'
    AUTHORIZATION_URL = 'https://www.dropbox.com/oauth2/authorize'
    ACCESS_TOKEN_URL = 'https://api.dropboxapi.com/oauth2/token'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False

    def get_user_details(self, response):
        """Return user details from Dropbox account"""
        name = response.get('name')
        return {'username': str(response.get('account_id')),
                'email': response.get('email'),
                'fullname': name.get('display_name'),
                'first_name': name.get('given_name'),
                'last_name': name.get('surname')}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json(
            'https://api.dropboxapi.com/2/users/get_current_account',
            headers={'Authorization': f'Bearer {access_token}'},
            method='POST'
        )
