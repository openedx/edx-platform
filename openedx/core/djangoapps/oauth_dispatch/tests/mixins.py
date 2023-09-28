"""
OAuth Dispatch test mixins
"""

import pytest
import jwt
from django.conf import settings
from jwkest.jwk import KEYS
from jwkest.jws import JWS
from jwt.exceptions import ExpiredSignatureError

from common.djangoapps.student.models import UserProfile, anonymous_id_for_user


class AccessTokenMixin:
    """ Mixin for tests dealing with OAuth 2 access tokens. """

    def assert_valid_jwt_access_token(self, access_token, user, scopes=None, should_be_expired=False, filters=None,
                                      should_be_asymmetric_key=False, should_be_restricted=None, aud=None, secret=None,
                                      expires_in=None, grant_type=None):
        """
        Verify the specified JWT access token is valid, and belongs to the specified user.
        Returns:
            dict: Decoded JWT payload
        """
        scopes = scopes or []
        audience = aud or settings.JWT_AUTH['JWT_AUDIENCE']
        secret_key = secret or settings.JWT_AUTH['JWT_SECRET_KEY']
        issuer = settings.JWT_AUTH['JWT_ISSUER']

        def _decode_jwt(verify_expiration):
            """
            Helper method to decode a JWT with the ability to
            verify the expiration of said token
            """
            keys = KEYS()
            if should_be_asymmetric_key:
                keys.load_jwks(settings.JWT_AUTH['JWT_PUBLIC_SIGNING_JWK_SET'])
            else:
                keys.add({'key': secret_key, 'kty': 'oct'})

            _ = JWS().verify_compact(access_token.encode('utf-8'), keys)

            return jwt.decode(
                access_token,
                secret_key,
                algorithms=[settings.JWT_AUTH['JWT_ALGORITHM']],
                audience=audience,
                issuer=issuer,
                options={
                    'verify_signature': False,
                    "verify_exp": verify_expiration
                },
            )

        # Note that if we expect the claims to have expired
        # then we ask the JWT library not to verify expiration
        # as that would throw a ExpiredSignatureError and
        # halt other verifications steps. We'll do a manual
        # expiry verification later on
        payload = _decode_jwt(verify_expiration=not should_be_expired)

        expected = {
            'aud': audience,
            'iss': issuer,
            'preferred_username': user.username,
            'scopes': scopes,
            'version': settings.JWT_AUTH['JWT_SUPPORTED_VERSION'],
            'sub': anonymous_id_for_user(user, None),
            'email_verified': user.is_active,
        }

        if 'user_id' in scopes:
            expected['user_id'] = user.id

        if 'email' in scopes:
            expected['email'] = user.email

        if 'profile' in scopes:
            try:
                name = UserProfile.objects.get(user=user).name
            except UserProfile.DoesNotExist:
                name = None

            expected.update({
                'name': name,
                'administrator': user.is_staff,
                'family_name': user.last_name,
                'given_name': user.first_name,
            })

        if filters:
            expected['filters'] = filters

        if should_be_restricted is not None:
            expected['is_restricted'] = should_be_restricted

        expected['grant_type'] = grant_type or ''

        self.assertDictContainsSubset(expected, payload)

        if expires_in:
            assert payload['exp'] == payload['iat'] + expires_in

        # Since we suppressed checking of expiry
        # in the claim in the above check, because we want
        # to fully examine the claims outside of the expiry,
        # now we should assert that the claim is indeed
        # expired
        if should_be_expired:
            with pytest.raises(ExpiredSignatureError):
                _decode_jwt(verify_expiration=True)

        return payload
