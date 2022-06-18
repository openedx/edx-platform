""" Tests for utility functions. """
import copy
from unittest import mock

import ddt
import jwt
from django.conf import settings
from django.test import TestCase, override_settings

from edx_rest_framework_extensions.auth.jwt.decoder import (
    decode_jwt_filters,
    decode_jwt_is_restricted,
    decode_jwt_scopes,
    jwt_decode_handler,
)
from edx_rest_framework_extensions.auth.jwt.tests.utils import (
    generate_jwt_token,
    generate_latest_version_payload,
    generate_unversioned_payload,
)
from edx_rest_framework_extensions.tests.factories import UserFactory


def exclude_from_jwt_auth_setting(key):
    """
    Clone the JWT_AUTH setting dict and remove the given key.
    """
    jwt_auth = copy.deepcopy(settings.JWT_AUTH)
    del jwt_auth[key]
    return jwt_auth


def update_jwt_auth_setting(jwt_auth_overrides):
    """
    Clone the JWT_AUTH setting dict and update it with the given overrides.
    """
    jwt_auth = copy.deepcopy(settings.JWT_AUTH)
    jwt_auth.update(jwt_auth_overrides)
    return jwt_auth


@ddt.ddt
class JWTDecodeHandlerTests(TestCase):
    """ Tests for the `jwt_decode_handler` utility function. """
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.payload = generate_latest_version_payload(self.user)
        self.jwt = generate_jwt_token(self.payload)

    def test_success(self):
        """
        Confirms that the format of the valid response from the token decoder matches the payload
        """
        self.assertDictEqual(jwt_decode_handler(self.jwt), self.payload)

    @ddt.data(*settings.JWT_AUTH['JWT_ISSUERS'])
    def test_valid_token_multiple_valid_issuers(self, jwt_issuer):
        """
        Validates that a valid token is properly decoded given a list of multiple valid issuers
        """

        # Verify that each valid issuer is properly matched against the valid issuers list
        # and used to decode the token that was generated using said valid issuer data
        self.payload['iss'] = jwt_issuer['ISSUER']
        token = generate_jwt_token(self.payload, jwt_issuer['SECRET_KEY'])
        self.assertEqual(jwt_decode_handler(token), self.payload)

    def test_failure_invalid_issuer(self):
        """
        Verifies the function logs decode failures with invalid issuer,
        and raises an InvalidTokenError if the token cannot be decoded
        """

        # Create tokens using each invalid issuer and attempt to decode them against
        # the valid issuers list, which won't work
        with mock.patch('edx_rest_framework_extensions.auth.jwt.decoder.logger') as patched_log:
            with self.assertRaises(jwt.InvalidTokenError):
                self.payload['iss'] = 'invalid-issuer'
                # signing key of None will use the default valid signing key
                valid_signing_key = None
                # Generate a token using the invalid issuer data
                token = generate_jwt_token(self.payload, valid_signing_key)
                # Attempt to decode the token against the entries in the valid issuers list,
                # which will fail with an InvalidTokenError
                jwt_decode_handler(token)

            msg = "Token decode failed due to mismatched issuer [%s]"
            patched_log.info.assert_any_call(msg, 'invalid-issuer')

    def test_failure_invalid_token(self):
        """
        Verifies the function logs decode failures, and raises an InvalidTokenError if the token cannot be decoded
        """

        # Create tokens using each invalid issuer and attempt to decode them against
        # the valid issuers list, which won't work
        with mock.patch('edx_rest_framework_extensions.auth.jwt.decoder.logger') as patched_log:
            with self.assertRaises(jwt.InvalidTokenError):
                # Attempt to decode an invalid token, which will fail with an InvalidTokenError
                jwt_decode_handler("invalid.token")

            patched_log.exception.assert_any_call("Token verification failed.")

    @override_settings(JWT_AUTH=exclude_from_jwt_auth_setting('JWT_SUPPORTED_VERSION'))
    def test_supported_jwt_version_not_specified(self):
        """
        Verifies the JWT is decoded successfully when the JWT_SUPPORTED_VERSION setting is not specified.
        """
        token = generate_jwt_token(self.payload)
        self.assertDictEqual(jwt_decode_handler(token), self.payload)

    @ddt.data(None, '0.5.0', '1.0.0', '1.0.5', '1.5.0', '1.5.5')
    def test_supported_jwt_version(self, jwt_version):
        """
        Verifies the JWT is decoded successfully with different supported versions in the token.
        """
        jwt_payload = generate_latest_version_payload(self.user, version=jwt_version)
        token = generate_jwt_token(jwt_payload)
        self.assertDictEqual(jwt_decode_handler(token), jwt_payload)

    @override_settings(JWT_AUTH=update_jwt_auth_setting({'JWT_SUPPORTED_VERSION': '0.5.0'}))
    def test_unsupported_jwt_version(self):
        """
        Verifies the function logs decode failures, and raises an
        InvalidTokenError if the token version is not supported.
        """
        with mock.patch('edx_rest_framework_extensions.auth.jwt.decoder.logger') as patched_log:
            with self.assertRaises(jwt.InvalidTokenError):
                token = generate_jwt_token(self.payload)
                jwt_decode_handler(token)

            msg = "Token decode failed due to unsupported JWT version number [%s]"
            patched_log.info.assert_any_call(msg, '1.1.0')

    def test_upgrade(self):
        """
        Verifies the JWT is upgraded when an old (starting) version is provided.
        """
        jwt_payload = generate_unversioned_payload(self.user)
        token = generate_jwt_token(jwt_payload)

        upgraded_payload = generate_latest_version_payload(self.user, version='1.0.0')

        # Keep time-related values constant for full-proof comparison.
        upgraded_payload['iat'], upgraded_payload['exp'] = jwt_payload['iat'], jwt_payload['exp']
        self.assertDictEqual(jwt_decode_handler(token), upgraded_payload)

    def test_failure_invalid_signature(self):
        """
        Verifies the function logs decode failures with invalid signature,
        and raises an InvalidTokenError if the token cannot be decoded
        """
        # Create tokens using each invalid signature and attempt to decode them against
        # the valid signature.
        with mock.patch('edx_rest_framework_extensions.auth.jwt.decoder.logger') as patched_log:
            with self.assertRaises(jwt.InvalidTokenError):
                invalid_signing_key = 'invalid-secret-key'

                # Generate a token using the invalid signing key data
                token = generate_jwt_token(self.payload, invalid_signing_key)
                # Attempt to decode the token against invalid signature,
                # which will fail with an InvalidTokenError
                jwt_decode_handler(token)

            patched_log.exception.assert_any_call("Token verification failed.")

    @ddt.data("exp", "iat")
    def test_required_claims(self, claim):
        """
        Verify that tokens that do not carry 'exp' or 'iat' claims are rejected
        """
        # Deletes required claim from payload
        del self.payload[claim]
        token = generate_jwt_token(self.payload)
        with self.assertRaises(jwt.MissingRequiredClaimError):
            # Decode to see if MissingRequiredClaimError exception is raised or not
            jwt_decode_handler(token)


def _jwt_decode_handler_with_defaults(token):  # pylint: disable=unused-argument
    """
    Accepts anything as a token and returns a fake JWT payload with defaults.
    """
    return {
        'scopes': ['fake:scope'],
        'is_restricted': True,
        'filters': ['fake:filter'],
    }


def _jwt_decode_handler_no_defaults(token):  # pylint: disable=unused-argument
    """
    Accepts anything as a token and returns a fake JWT payload with no defaults.
    """
    return {}


@ddt.ddt
class JWTDecodeHandlerSettingTests(TestCase):
    """
    Tests to ensure utility functions respect JWT_DECODE_HANDLER setting.

    Note: An attempt was made to use ``override_settings`` to actually set
    ``JWT_DECODE_HANDLER``, but clean-up of the tests in tearDown was not working,
    even after reloading the module, and it was failing other tests in the test suite.
    """
    NORMALLY_INVALID_TOKEN = 'this is a valid jwt only with fake_jwt_decode_handler'

    @ddt.data(
        ('_jwt_decode_handler_with_defaults', ['fake:scope']),
        ('_jwt_decode_handler_no_defaults', [])
    )
    @ddt.unpack
    @mock.patch('edx_rest_framework_extensions.auth.jwt.decoder.api_settings')
    def test_decode_jwt_scopes(self, jwt_decode_handler_name, expected_scope, mock_api_settings):
        mock_api_settings.JWT_DECODE_HANDLER = globals()[jwt_decode_handler_name]
        scopes = decode_jwt_scopes(self.NORMALLY_INVALID_TOKEN)
        self.assertEqual(scopes, expected_scope)

    @ddt.data(
        ('_jwt_decode_handler_with_defaults', True),
        ('_jwt_decode_handler_no_defaults', False)
    )
    @ddt.unpack
    @mock.patch('edx_rest_framework_extensions.auth.jwt.decoder.api_settings')
    def test_decode_jwt_is_restricted(self, jwt_decode_handler_name, expected_is_restricted, mock_api_settings):
        mock_api_settings.JWT_DECODE_HANDLER = globals()[jwt_decode_handler_name]
        is_restricted = decode_jwt_is_restricted(self.NORMALLY_INVALID_TOKEN)
        self.assertEqual(is_restricted, expected_is_restricted)

    @ddt.data(
        ('_jwt_decode_handler_with_defaults', [['fake', 'filter']]),
        ('_jwt_decode_handler_no_defaults', [])
    )
    @ddt.unpack
    @mock.patch('edx_rest_framework_extensions.auth.jwt.decoder.api_settings')
    def test_decode_jwt_filters(self, jwt_decode_handler_name, expected_filter, mock_api_settings):
        mock_api_settings.JWT_DECODE_HANDLER = globals()[jwt_decode_handler_name]
        filters = decode_jwt_filters(self.NORMALLY_INVALID_TOKEN)
        self.assertEqual(filters, expected_filter)
