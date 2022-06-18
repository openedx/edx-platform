"""
Gitea OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/gitea.html
"""
from .oauth import BaseOAuth2


class GiteaOAuth2   (BaseOAuth2):
    """Gitea OAuth authentication backend"""

    name = 'gitea'
    API_URL = 'https://gitea.com'
    AUTHORIZATION_URL = 'https://gitea.com/login/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://gitea.com/login/oauth/access_token'
    ACCESS_TOKEN_METHOD = 'POST'
    SCOPE_SEPARATOR = ','
    REDIRECT_STATE = False
    STATE_PARAMETER = True
    EXTRA_DATA = [
        ('id', 'id'),
        ('expires_in', 'expires'),
        ('refresh_token', 'refresh_token')
    ]

    def api_url(self, path):
        api_url = self.setting('API_URL') or self.API_URL
        return '{}{}'.format(api_url.rstrip('/'), path)

    def authorization_url(self):
        return self.api_url('/login/oauth/authorize')

    def access_token_url(self):
        return self.api_url('/login/oauth/access_token')

    def get_user_details(self, response):
        """Return user details from Gitea account"""
        fullname, first_name, last_name = self.get_user_names(
            response.get('fullname')
        )
        return {'username': response.get('login'),
                'email': response.get('email') or '',
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json(self.api_url('/api/v1/user'), params={
            'access_token': access_token
        })

