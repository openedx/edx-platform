"""
SimpleLogin OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/simplelogin.html
"""

from .oauth import BaseOAuth2


class SimpleLoginOAuth2(BaseOAuth2):
    """SimpleLogin OAuth authentication backend"""
    name = 'simplelogin'
    AUTHORIZATION_URL = 'https://app.simplelogin.io/oauth2/authorize'
    ACCESS_TOKEN_URL = 'https://app.simplelogin.io/oauth2/token'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False
    STATE_PARAMETER = True
    SEND_USER_AGENT = True
    EXTRA_DATA = [
        ('name', 'name'),
        ('email', 'email'),
        ('avatar_url', 'avatar_url'),
    ]

    # endpoint to get user info
    USERINFO_URL = 'https://app.simplelogin.io/oauth2/userinfo'

    def get_user_details(self, response):
        """Return user details from SimpleLogin account"""
        fullname, first_name, last_name = self.get_user_names(
            response.get('name')
        )
        return {
            'username': response.get('email'),
            'email': response.get('email'),
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json(self.USERINFO_URL, params={
            'access_token': access_token
        })
