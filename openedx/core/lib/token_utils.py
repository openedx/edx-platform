"""Utilities for working with ID tokens."""
from time import time

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from django.conf import settings
from django.utils.functional import cached_property
import jwt

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from student.models import UserProfile, anonymous_id_for_user


class JwtBuilder(object):
    """Utility for building JWTs.

    Unifies diverse approaches to JWT creation in a single class. This utility defaults to using the system's
    JWT configuration.

    NOTE: This utility class will allow you to override the signing key and audience claim to support those
    clients which still require this. This approach to JWT creation is DEPRECATED. Avoid doing this for new clients.

    Arguments:
        user (User): User for which to generate the JWT.

    Keyword Arguments:
        asymmetric (Boolean): Whether the JWT should be signed with this app's private key.
        secret (string): Overrides configured JWT secret (signing) key. Unused if an asymmetric signature is requested.
    """
    def __init__(self, user, asymmetric=False, secret=None):
        self.user = user
        self.asymmetric = asymmetric
        self.secret = secret
        self.jwt_auth = configuration_helpers.get_value('JWT_AUTH', settings.JWT_AUTH)

    def build_token(self, scopes, expires_in, aud=None):
        """Returns a JWT access token.

        Arguments:
            scopes (list): Scopes controlling which optional claims are included in the token.
            expires_in (int): Time to token expiry, specified in seconds.

        Keyword Arguments:
            aud (string): Overrides configured JWT audience claim.
        """
        now = int(time())
        payload = {
            'aud': aud if aud else self.jwt_auth['JWT_AUDIENCE'],
            'exp': now + expires_in,
            'iat': now,
            'iss': self.jwt_auth['JWT_ISSUER'],
            'preferred_username': self.user.username,
            'scopes': scopes,
            'sub': anonymous_id_for_user(self.user, None),
        }

        for scope in scopes:
            handler = self.claim_handlers.get(scope)

            if handler:
                handler(payload)

        return self.encode(payload)

    @cached_property
    def claim_handlers(self):
        """Returns a dictionary mapping scopes to methods that will add claims to the JWT payload."""

        return {
            'email': self.attach_email_claim,
            'profile': self.attach_profile_claim
        }

    def attach_email_claim(self, payload):
        """Add the email claim details to the JWT payload."""
        payload['email'] = self.user.email

    def attach_profile_claim(self, payload):
        """Add the profile claim details to the JWT payload."""
        try:
            # Some users (e.g., service users) may not have user profiles.
            name = UserProfile.objects.get(user=self.user).name
        except UserProfile.DoesNotExist:
            name = None

        payload.update({
            'name': name,
            'administrator': self.user.is_staff,
        })

    def encode(self, payload):
        """Encode the provided payload."""
        if self.asymmetric:
            secret = load_pem_private_key(settings.PRIVATE_RSA_KEY, None, default_backend())
            algorithm = 'RS512'
        else:
            secret = self.secret if self.secret else self.jwt_auth['JWT_SECRET_KEY']
            algorithm = self.jwt_auth['JWT_ALGORITHM']

        return jwt.encode(payload, secret, algorithm=algorithm)
