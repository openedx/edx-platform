from social_core.backends.oauth import BaseOAuth2


class CognitoOAuth2(BaseOAuth2):
    name = 'cognito'
    ID_KEY = 'username'
    DEFAULT_SCOPE = ['openid', 'profile', 'email']
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False

    def user_pool_domain(self):
        return self.setting('POOL_DOMAIN')

    def authorization_url(self):
        return f'{self.user_pool_domain()}/login'

    def access_token_url(self):
        return f'{self.user_pool_domain()}/oauth2/token'

    def user_data_url(self):
        return f'{self.user_pool_domain()}/oauth2/userInfo'

    def get_user_details(self, response):
        """Return user details from their cognito pool account"""
        first_name = response.get('given_name') or ''
        last_name = response.get('family_name') or ''
        fullname, first_name, last_name = self.get_user_names(
            first_name=first_name,
            last_name=last_name,
        )
        return {'username': response.get('username') or response.get('email'),
                'email': response.get('email'),
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        """Grab user profile information from cognito."""
        response = self.get_json(
            url=self.user_data_url(),
            headers={'Authorization': f'Bearer {access_token}'},
        )

        user_data = {
            'given_name': response.get('given_name'),
            'family_name': response.get('family_name'),
            'username': response.get('username'),
            'email': response.get('email'),
        }

        return user_data
