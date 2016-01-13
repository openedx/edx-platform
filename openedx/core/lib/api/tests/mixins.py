"""
Mixins for API Authentication tests.
"""
from time import time

from django.conf import settings
import jwt


JWT_AUTH = 'JWT_AUTH'


class JwtMixin(object):
    """ Mixin with JWT-related helper functions. """

    @property
    def jwt_settings(self):
        """This property will return JWT settings"""
        return getattr(settings, JWT_AUTH)

    def generate_token(self, payload, secret=None):
        """Generate a JWT token with the provided payload."""
        secret = secret or self.jwt_settings['JWT_SECRET_KEY']
        token = jwt.encode(payload, secret)
        return token

    def generate_id_token(self, user, admin=False, ttl=1, **overrides):
        """Generate a JWT id_token that looks like the ones currently
        returned by the edx oidc provider."""

        payload = self.default_payload(user=user, admin=admin, ttl=ttl)
        payload.update(overrides)
        return self.generate_token(payload)

    def default_payload(self, user, admin=False, ttl=1):
        """Generate a bare payload, in case tests need to manipulate
        it directly before encoding."""
        now = int(time())

        return {
            "iss": self.jwt_settings['JWT_ISSUER'],
            "sub": user.pk,
            "aud": self.jwt_settings['JWT_AUDIENCE'],
            "nonce": "dummy-nonce",
            "exp": now + ttl,
            "iat": now,
            "preferred_username": user.username,
            "administrator": admin,
            "email": user.email,
            "locale": "en",
            "name": user.first_name + " " + user.last_name,
            "given_name": "",
            "family_name": "",
        }
