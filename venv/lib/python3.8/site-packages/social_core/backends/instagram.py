"""
Instagram OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/instagram.html
"""
from .oauth import BaseOAuth2


class InstagramOAuth2(BaseOAuth2):
    name = 'instagram'
    AUTHORIZATION_URL = 'https://api.instagram.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://api.instagram.com/oauth/access_token'
    ACCESS_TOKEN_METHOD = 'POST'

    def get_user_id(self, details, response):
        user = response.get('user') or {}
        return user.get('id')

    def get_user_details(self, response):
        """Return user details from Instagram account"""
        user = response.get('user') or {}
        username = user['username']
        email = user.get('email', '')
        fullname, first_name, last_name = self.get_user_names(
            user.get('full_name', '')
        )
        return {'username': username,
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name,
                'email': email}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        # For more fields see:
        # https://developers.facebook.com/docs/instagram-basic-display-api/reference/user#fields
        # In fact there are not very many of them.
        fields = 'id,username'
        params = {'access_token': access_token, 'fields': fields}
        response = self.get_json('https://graph.instagram.com/me',
                             params=params)
        return {'user': response}

    def auth_html(self):
        pass
