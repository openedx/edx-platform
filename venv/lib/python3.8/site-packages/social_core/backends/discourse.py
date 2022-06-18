import hmac
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode
from hashlib import sha256
from urllib.parse import urlencode

from ..exceptions import AuthException, AuthTokenError
from ..utils import parse_qs
from .base import BaseAuth


class DiscourseAuth(BaseAuth):
    name = 'discourse'
    EXTRA_DATA = ['username', 'name', 'avatar_url']

    def auth_url(self):
        """
        Get the URL to which we must redirect in order to authenticate the user
        """
        return_url = self.redirect_uri
        nonce = self.strategy.random_string(64)
        self.add_nonce(nonce)

        payload = urlencode({
            'nonce': nonce,
            'return_sso_url': return_url
        })
        base_64_payload = urlsafe_b64encode(
            payload.encode('utf8')
        ).decode('ascii')

        payload_signature = hmac.new(
            self.setting('SECRET').encode('utf8'),
            base_64_payload.encode('utf8'),
            sha256,
        ).hexdigest()
        encoded_params = urlencode({
            'sso': base_64_payload,
            'sig': payload_signature
        })
        return f'{self.get_idp_url()}?{encoded_params}'

    def get_idp_url(self):
        return self.setting('SERVER_URL') + '/session/sso_provider'

    def get_user_id(self, details, response):
        return response['email']

    def get_user_details(self, response):
        results = {
            'username': response.get('username'),
            'email': response.get('email'),
            'name': response.get('name'),
            'groups': response.get('groups', '').split(','),
            'is_staff': response.get('admin') == 'true' or
                        response.get('moderator') == 'true',
            'is_superuser': response.get('admin') == 'true',
        }
        return results

    def add_nonce(self, nonce):
        self.strategy.storage.nonce.use(
            self.setting('SERVER_URL'),
            time.time(),
            nonce
        )

    def get_nonce(self, nonce):
        return self.strategy.storage.nonce.get(
            self.setting('SERVER_URL'),
            nonce
        )

    def delete_nonce(self, nonce):
        self.strategy.storage.nonce.delete(nonce)

    def auth_complete(self, *args, **kwargs):
        """
        The user has been redirected back from the IdP and we should
        now log them in, if everything checks out.
        """
        request_data = self.strategy.request_data()

        sso_params = request_data.get('sso')
        sso_signature = request_data.get('sig')

        param_signature = hmac.new(
            self.setting('SECRET').encode('utf8'),
            sso_params.encode('utf8'),
            sha256
        ).hexdigest()

        if not hmac.compare_digest(str(sso_signature), str(param_signature)):
            raise AuthException('Could not verify discourse login')

        decoded_params = urlsafe_b64decode(
            sso_params.encode('utf8')
        ).decode('ascii')

        # Validate the nonce to ensure the request was not modified
        response = parse_qs(decoded_params)
        nonce_obj = self.get_nonce(response.get('nonce'))
        if nonce_obj:
            self.delete_nonce(nonce_obj)
        else:
            raise AuthTokenError(self, 'Incorrect id_token: nonce')

        kwargs.update({
            'sso': '',
            'sig': '',
            'backend': self,
            'response': response
        })
        return self.strategy.authenticate(*args, **kwargs)
