"""
OAuth Dispatch test mixins
"""
import jwt
from django.conf import settings


class AccessTokenMixin(object):
    """ Mixin for tests dealing with OAuth 2 access tokens. """

    def assert_valid_jwt_access_token(self, access_token, user, scopes=None):
        """
        Verify the specified JWT access token is valid, and belongs to the specified user.

        Args:
            access_token (str): JWT
            user (User): User whose information is contained in the JWT payload.

        Returns:
            dict: Decoded JWT payload
        """
        scopes = scopes or []
        audience = settings.JWT_AUTH['JWT_AUDIENCE']
        issuer = settings.JWT_AUTH['JWT_ISSUER']
        payload = jwt.decode(
            access_token,
            settings.JWT_AUTH['JWT_SECRET_KEY'],
            algorithms=[settings.JWT_AUTH['JWT_ALGORITHM']],
            audience=audience,
            issuer=issuer
        )

        expected = {
            'aud': audience,
            'iss': issuer,
            'preferred_username': user.username,
            'scopes': scopes,
        }

        if 'email' in scopes:
            expected['email'] = user.email

        self.assertDictContainsSubset(expected, payload)

        return payload
