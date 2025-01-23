"""
Tests for token handling
"""
import unittest

from django.conf import settings
from jwkest import BadSignature, Expired, Invalid, MissingKey, jwk
from jwkest.jws import JWS

from openedx.core.djangolib.testing.utils import skip_unless_lms
from openedx.core.lib.jwt import _encode_and_sign, create_jwt, unpack_jwt


test_user_id = 121
invalid_test_user_id = 120
test_timeout = 60
test_now = 1661432902
test_claims = {"foo": "bar", "baz": "quux", "meaning": 42}
expected_full_token = {
    "lms_user_id": test_user_id,
    "iat": 1661432902,
    "exp": 1661432902 + 60,
    "iss": "token-test-issuer",  # these lines from test_settings.py
    "version": "1.2.0",  # these lines from test_settings.py
}


@skip_unless_lms
class TestSign(unittest.TestCase):
    """
    Tests for JWT creation and signing.
    """

    def test_create_jwt(self):
        token = create_jwt(test_user_id, test_timeout, {}, test_now)

        decoded = _verify_jwt(token)
        self.assertEqual(expected_full_token, decoded)

    def test_create_jwt_with_claims(self):
        token = create_jwt(test_user_id, test_timeout, test_claims, test_now)

        expected_token_with_claims = expected_full_token.copy()
        expected_token_with_claims.update(test_claims)

        decoded = _verify_jwt(token)
        self.assertEqual(expected_token_with_claims, decoded)

    def test_malformed_token(self):
        token = create_jwt(test_user_id, test_timeout, test_claims, test_now)
        token = token + "a"

        expected_token_with_claims = expected_full_token.copy()
        expected_token_with_claims.update(test_claims)

        with self.assertRaises(BadSignature):
            _verify_jwt(token)


def _verify_jwt(jwt_token):
    """
    Helper function which verifies the signature and decodes the token
    from string back to claims form
    """
    keys = jwk.KEYS()
    keys.load_jwks(settings.TOKEN_SIGNING['JWT_PUBLIC_SIGNING_JWK_SET'])
    decoded = JWS().verify_compact(jwt_token.encode('utf-8'), keys)
    return decoded


@skip_unless_lms
class TestUnpack(unittest.TestCase):
    """
    Tests for JWT unpacking.
    """

    def test_unpack_jwt(self):
        token = create_jwt(test_user_id, test_timeout, {}, test_now)
        decoded = unpack_jwt(token, test_user_id, test_now)

        self.assertEqual(expected_full_token, decoded)

    def test_unpack_jwt_with_claims(self):
        token = create_jwt(test_user_id, test_timeout, test_claims, test_now)

        expected_token_with_claims = expected_full_token.copy()
        expected_token_with_claims.update(test_claims)

        decoded = unpack_jwt(token, test_user_id, test_now)

        self.assertEqual(expected_token_with_claims, decoded)

    def test_malformed_token(self):
        token = create_jwt(test_user_id, test_timeout, test_claims, test_now)
        token = token + "a"

        expected_token_with_claims = expected_full_token.copy()
        expected_token_with_claims.update(test_claims)

        with self.assertRaises(BadSignature):
            unpack_jwt(token, test_user_id, test_now)

    def test_unpack_token_with_invalid_user(self):
        token = create_jwt(invalid_test_user_id, test_timeout, {}, test_now)

        with self.assertRaises(Invalid):
            unpack_jwt(token, test_user_id, test_now)

    def test_unpack_expired_token(self):
        token = create_jwt(test_user_id, test_timeout, {}, test_now)

        with self.assertRaises(Expired):
            unpack_jwt(token, test_user_id, test_now + test_timeout + 1)

    def test_missing_expired_lms_user_id(self):
        payload = expected_full_token.copy()
        del payload['lms_user_id']
        token = _encode_and_sign(payload)

        with self.assertRaises(MissingKey):
            unpack_jwt(token, test_user_id, test_now)

    def test_missing_expired_key(self):
        payload = expected_full_token.copy()
        del payload['exp']
        token = _encode_and_sign(payload)

        with self.assertRaises(MissingKey):
            unpack_jwt(token, test_user_id, test_now)
