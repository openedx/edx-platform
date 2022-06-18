from urllib.parse import urljoin

from social_core.utils import cache

from ..utils import append_slash
from .open_id_connect import OpenIdConnectAuth


class Fence(OpenIdConnectAuth):

    name = 'fence'
    OIDC_ENDPOINT = 'https://nci-crdc.datacommons.io'
    ID_KEY = 'username'
    ACCESS_TOKEN_METHOD = 'POST'
    DEFAULT_SCOPE = ['openid', 'user']
    JWT_DECODE_OPTIONS = {'verify_at_hash': False}

    def _url(self, path):
        return urljoin(append_slash(self.OIDC_ENDPOINT), path)

    def authorization_url(self):
        return self._url('user/oauth2/authorize')

    def access_token_url(self):
        return self._url('user/oauth2/token')

    @cache(ttl=86400)
    def oidc_config(self):
        return self.get_json(self._url('.well-known/openid-configuration'))

    def get_user_details(self, response):
        return {
            'username': response.get('preferred_username'),
            'email': response.get('username'),
            'fullname': response.get('name'),
            'first_name': response.get('given_name'),
            'last_name': response.get('family_name'),
        }
