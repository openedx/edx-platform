import base64

from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_der_x509_certificate
from jwt import DecodeError, ExpiredSignatureError
from jwt import decode as jwt_decode
from jwt import get_unverified_header

from ..exceptions import AuthTokenError
from .azuread import AzureADOAuth2

"""
Copyright (c) 2015 Microsoft Open Technologies, Inc.

All rights reserved.

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

"""
Azure AD OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/azuread.html

See https://nicksnettravels.builttoroam.com/post/2017/01/24/Verifying-Azure-Active-Directory-JWT-Tokens.aspx
for verifying JWT tokens.
"""


class AzureADTenantOAuth2(AzureADOAuth2):
    name = 'azuread-tenant-oauth2'
    OPENID_CONFIGURATION_URL = \
        'https://login.microsoftonline.com/{tenant_id}/.well-known/openid-configuration'
    AUTHORIZATION_URL = \
        'https://login.microsoftonline.com/{tenant_id}/oauth2/authorize'
    ACCESS_TOKEN_URL = 'https://login.microsoftonline.com/{tenant_id}/oauth2/token'
    JWKS_URL = 'https://login.microsoftonline.com/{tenant_id}/discovery/keys'

    @property
    def tenant_id(self):
        return self.setting('TENANT_ID', 'common')

    def openid_configuration_url(self):
        return self.OPENID_CONFIGURATION_URL.format(tenant_id=self.tenant_id)

    def authorization_url(self):
        return self.AUTHORIZATION_URL.format(tenant_id=self.tenant_id)

    def access_token_url(self):
        return self.ACCESS_TOKEN_URL.format(tenant_id=self.tenant_id)

    def jwks_url(self):
        return self.JWKS_URL.format(tenant_id=self.tenant_id)

    def get_certificate(self, kid):
        # retrieve keys from jwks_url
        resp = self.request(self.jwks_url(), method='GET')
        resp.raise_for_status()

        # find the proper key for the kid
        for key in resp.json()['keys']:
            if key['kid'] == kid:
                x5c = key['x5c'][0]
                break
        else:
            raise DecodeError(f'Cannot find kid={kid}')

        return load_der_x509_certificate(base64.b64decode(x5c),
                                         default_backend())

    def get_user_id(self, details, response):
        """Use subject (sub) claim as unique id."""
        return response.get('sub')

    def user_data(self, access_token, *args, **kwargs):
        response = kwargs.get('response')
        id_token = response.get('id_token')

        # get key id and algorithm
        key_id = get_unverified_header(id_token)['kid']

        try:
            # retrieve certificate for key_id
            certificate = self.get_certificate(key_id)

            return jwt_decode(
                id_token,
                key=certificate.public_key(),
                algorithms=['RS256'],
                audience=self.setting('KEY')
            )
        except (DecodeError, ExpiredSignatureError) as error:
            raise AuthTokenError(self, error)


class AzureADV2TenantOAuth2(AzureADTenantOAuth2):
    name = 'azuread-v2-tenant-oauth2'
    OPENID_CONFIGURATION_URL = \
        'https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid-configuration'
    AUTHORIZATION_URL = 'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize'
    ACCESS_TOKEN_URL = 'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'
    JWKS_URL = 'https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys'
    DEFAULT_SCOPE = ['openid', 'profile', 'offline_access']

    def get_user_id(self, details, response):
        """Use upn as unique id"""
        return response.get('preferred_username')

    def get_user_details(self, response):
        """Return user details from Azure AD account"""
        fullname, first_name, last_name = (
            response.get('name', ''),
            response.get('given_name', ''),
            response.get('family_name', '')
        )
        return {'username': fullname,
                'email': response.get('preferred_username'),
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}
