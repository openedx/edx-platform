from .oauth import BaseOAuth2


class NaverOAuth2(BaseOAuth2):
    """Naver OAuth authentication backend"""
    name = 'naver'
    AUTHORIZATION_URL = 'https://nid.naver.com/oauth2.0/authorize'
    ACCESS_TOKEN_URL = 'https://nid.naver.com/oauth2.0/token'
    ACCESS_TOKEN_METHOD = 'POST'
    EXTRA_DATA = [
        ('id', 'id'),
    ]

    def get_user_id(self, details, response):
        return response.get('id')

    def get_user_details(self, response):
        """Return user details from Naver account"""
        return {
            'username': response.get('username'),
            'email': response.get('email'),
            'fullname': response.get('username'),
        }

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        response = self.request(
            'https://openapi.naver.com/v1/nid/me',
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content_Type': 'text/json'
            }
        )

        data = response.json()

        return {
            'id': self._fetch(data, 'id'),
            'email': self._fetch(data, 'email'),
            'username': self._fetch(data, 'name'),
            'nickname': self._fetch(data, 'nickname'),
            'gender': self._fetch(data, 'gender'),
            'age': self._fetch(data, 'age'),
            'birthday': self._fetch(data, 'birthday'),
            'profile_image': self._fetch(data, 'profile_image')
        }

    def auth_headers(self):
        client_id, client_secret = self.get_key_and_secret()
        return {
            'grant_type': 'authorization_code',
            'code': self.data.get('code'),
            'client_id': client_id,
            'client_secret': client_secret,
        }

    def _fetch(self, data, key):
        try:
            return data['response'][key]
        except (KeyError, TypeError):
            return ''
