"""
Sign In With Apple authentication backend.

Docs:
    * https://developer.apple.com/documentation/signinwithapplerestapi
    * https://developer.apple.com/documentation/signinwithapplerestapi/tokenresponse

Settings:
    * `TEAM` - your team id;
    * `KEY` - your key id;
    * `CLIENT` - your client id;
    * `AUDIENCE` - a list of authorized client IDs, defaults to [CLIENT].
                   Use this if you need to accept both service and bundle id to
                   be able to login both via iOS and ie a web form.
    * `SECRET` - your secret key;
    * `SCOPE` (optional) - e.g. `['name', 'email']`;
    * `EMAIL_AS_USERNAME` - use apple email is username is set, use apple id
                            otherwise.
    * `AppleIdAuth.TOKEN_TTL_SEC` - time before JWT token expiration, seconds.
    * `SOCIAL_AUTH_APPLE_ID_INACTIVE_USER_LOGIN` - allow inactive users email to
                                                   login
"""

import json
import time

import jwt
from jwt.algorithms import RSAAlgorithm
from jwt.exceptions import PyJWTError

from social_core.backends.oauth import BaseOAuth2
from social_core.exceptions import AuthFailed


class AppleIdAuth(BaseOAuth2):
    name = 'apple-id'

    JWK_URL = 'https://appleid.apple.com/auth/keys'
    AUTHORIZATION_URL = 'https://appleid.apple.com/auth/authorize'
    ACCESS_TOKEN_URL = 'https://appleid.apple.com/auth/token'
    ACCESS_TOKEN_METHOD = 'POST'
    RESPONSE_MODE = None

    ID_KEY = 'sub'
    TOKEN_KEY = 'id_token'
    STATE_PARAMETER = True
    REDIRECT_STATE = False
    SCOPE_SEPARATOR = '%20'

    TOKEN_AUDIENCE = 'https://appleid.apple.com'
    TOKEN_TTL_SEC = 6 * 30 * 24 * 60 * 60

    def get_audience(self):
        client_id = self.setting('CLIENT')
        return self.setting('AUDIENCE', default=[client_id])

    def auth_params(self, *args, **kwargs):
        """
        Apple requires to set `response_mode` to `form_post` if `scope`
        parameter is passed.
        """
        params = super().auth_params(*args, **kwargs)
        if self.RESPONSE_MODE:
            params['response_mode'] = self.RESPONSE_MODE
        elif self.get_scope():
            params['response_mode'] = 'form_post'
        return params

    def get_private_key(self):
        """
        Return contents of the private key file. Override this method to provide
        secret key from another source if needed.
        """
        return self.setting('SECRET')

    def generate_client_secret(self):
        now = int(time.time())
        client_id = self.setting('CLIENT')
        team_id = self.setting('TEAM')
        key_id = self.setting('KEY')
        private_key = self.get_private_key()

        headers = {'kid': key_id}
        payload = {
            'iss': team_id,
            'iat': now,
            'exp': now + self.TOKEN_TTL_SEC,
            'aud': self.TOKEN_AUDIENCE,
            'sub': client_id,
        }

        return jwt.encode(payload, key=private_key, algorithm='ES256',
                          headers=headers)

    def get_key_and_secret(self):
        client_id = self.setting('CLIENT')
        client_secret = self.generate_client_secret()
        return client_id, client_secret

    def get_apple_jwk(self, kid=None):
        """
        Return requested Apple public key or all available.
        """
        keys = self.get_json(url=self.JWK_URL).get('keys')

        if not isinstance(keys, list) or not keys:
            raise AuthFailed(self, 'Invalid jwk response')

        if kid:
            return json.dumps([key for key in keys if key['kid'] == kid][0])
        else:
            return (json.dumps(key) for key in keys)

    def decode_id_token(self, id_token):
        """
        Decode and validate JWT token from apple and return payload including
        user data.
        """
        if not id_token:
            raise AuthFailed(self, 'Missing id_token parameter')

        try:
            kid = jwt.get_unverified_header(id_token).get('kid')
            public_key = RSAAlgorithm.from_jwk(self.get_apple_jwk(kid))
            decoded = jwt.decode(
                id_token,
                key=public_key,
                audience=self.get_audience(),
                algorithms=['RS256'],
            )
        except PyJWTError as error:
            raise AuthFailed(self, f'Token validation failed by {error}')

        return decoded

    def get_user_details(self, response):
        name = json.loads(self.data.get('user', '{}')).get('name', {})
        fullname, first_name, last_name = self.get_user_names(
            fullname='',
            first_name=name.get('firstName', ''),
            last_name=name.get('lastName', '')
        )

        email = response.get('email', '')
        apple_id = response.get(self.ID_KEY, '')
        # prevent updating User with empty strings
        user_details = {
            'fullname': fullname or None,
            'first_name': first_name or None,
            'last_name': last_name or None,
            'email': email,
        }
        if email and self.setting('EMAIL_AS_USERNAME'):
            user_details['username'] = email
        if apple_id and not self.setting('EMAIL_AS_USERNAME'):
            user_details['username'] = apple_id

        return user_details

    def do_auth(self, access_token, *args, **kwargs):
        response = kwargs.pop('response', None) or {}
        jwt_string = response.get(self.TOKEN_KEY) or access_token

        if not jwt_string:
            raise AuthFailed(self, 'Missing id_token parameter')

        decoded_data = self.decode_id_token(jwt_string)
        return super().do_auth(access_token, response=decoded_data, *args, **kwargs)
