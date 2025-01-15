"""
JWT Token handling and signing functions.
"""

import json
from time import time

from django.conf import settings
from jwkest import Expired, Invalid, MissingKey, jwk
from jwkest.jws import JWS


def create_jwt(lms_user_id, expires_in_seconds, additional_token_claims, now=None):
    """
    Produce an encoded JWT (string) indicating some temporary permission for the indicated user.

    What permission that is must be encoded in additional_claims.
    Arguments:
        lms_user_id (int): LMS user ID this token is being generated for
        expires_in_seconds (int): Time to token expiry, specified in seconds.
        additional_token_claims (dict): Additional claims to include in the token.
        now(int): optional now value for testing
    """
    now = now or int(time())

    payload = {
        'lms_user_id': lms_user_id,
        'exp': now + expires_in_seconds,
        'iat': now,
        'iss': settings.TOKEN_SIGNING['JWT_ISSUER'],
        'version': settings.TOKEN_SIGNING['JWT_SUPPORTED_VERSION'],
    }
    payload.update(additional_token_claims)
    return _encode_and_sign(payload)


def _encode_and_sign(payload):
    """
    Encode and sign the provided payload.

    The signing key and algorithm are pulled from settings.
    """
    keys = jwk.KEYS()

    serialized_keypair = json.loads(settings.TOKEN_SIGNING['JWT_PRIVATE_SIGNING_JWK'])
    keys.add(serialized_keypair)
    algorithm = settings.TOKEN_SIGNING['JWT_SIGNING_ALGORITHM']

    data = json.dumps(payload)
    jws = JWS(data, alg=algorithm)
    return jws.sign_compact(keys=keys)


def unpack_jwt(token, lms_user_id, now=None):
    """
    Unpack and verify an encoded JWT.

    Validate the user and expiration.

    Arguments:
        token (string): The token to be unpacked and verified.
        lms_user_id (int): LMS user ID this token should match with.
        now (int): Optional now value for testing.

    Returns a valid, decoded json payload (string).
    """
    now = now or int(time())
    payload = _unpack_and_verify(token)

    if "lms_user_id" not in payload:
        raise MissingKey("LMS user id is missing")
    if "exp" not in payload:
        raise MissingKey("Expiration is missing")
    if payload["lms_user_id"] != lms_user_id:
        raise Invalid("User does not match")
    if payload["exp"] < now:
        raise Expired("Token is expired")

    return payload


def _unpack_and_verify(token):
    """
    Unpack and verify the provided token.

    The signing key and algorithm are pulled from settings.
    """
    keys = jwk.KEYS()
    keys.load_jwks(settings.TOKEN_SIGNING['JWT_PUBLIC_SIGNING_JWK_SET'])
    decoded = JWS().verify_compact(token.encode('utf-8'), keys)
    return decoded
