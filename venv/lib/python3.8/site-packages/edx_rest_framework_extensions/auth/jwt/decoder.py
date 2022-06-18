""" JWT decoder utility functions. """
import logging
import sys

import jwt
from django.conf import settings
from jwkest.jwk import KEYS
from jwkest.jws import JWS
from rest_framework_jwt.settings import api_settings
from semantic_version import Version

from edx_rest_framework_extensions.settings import get_first_jwt_issuer, get_jwt_issuers


logger = logging.getLogger(__name__)


class JwtTokenVersion:
    default_latest_supported = '1.2.0'

    starting_version = '1.0.0'
    added_version = '1.1.0'


def jwt_decode_handler(token):
    """
    Decodes a JSON Web Token (JWT).

    Notes:
        * Requires "exp" and "iat" claims to be present in the token's payload.
        * Aids debugging by logging InvalidTokenError log entries when decoding fails.

    Examples:
        Use with `djangorestframework-jwt <https://getblimp.github.io/django-rest-framework-jwt/>`_, by changing
        your Django settings:

        .. code-block:: python

            JWT_AUTH = {
                'JWT_DECODE_HANDLER': 'edx_rest_framework_extensions.auth.jwt.decoder.jwt_decode_handler',
                'JWT_ISSUER': 'https://the.jwt.issuer',
                'JWT_SECRET_KEY': 'the-jwt-secret-key',  (defaults to settings.SECRET_KEY)
                'JWT_AUDIENCE': 'the-jwt-audience',
                'JWT_PUBLIC_SIGNING_JWK_SET': 'the-jwk-set-of-public-signing-keys',
            }

    Warning:
        Do **not** use this method internally.  Only use it in ``JWT_DECODE_HANDLER`` like the above example.
        Internally, use ``configured_jwt_decode_handler`` which respects the ``JWT_DECODE_HANDLER`` setting.

    Args:
        token (str): JWT to be decoded.

    Returns:
        dict: Decoded JWT payload.

    Raises:
        MissingRequiredClaimError: Either the exp or iat claims is missing from the JWT payload.
        InvalidTokenError: Decoding fails.
    """
    jwt_issuer = get_first_jwt_issuer()
    _verify_jwt_signature(token, jwt_issuer)
    decoded_token = _decode_and_verify_token(token, jwt_issuer)
    return _set_token_defaults(decoded_token)


def configured_jwt_decode_handler(token):
    """
    Calls the ``jwt_decode_handler`` configured in the ``JWT_DECODE_HANDLER`` setting.
    """
    api_setting_jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
    return api_setting_jwt_decode_handler(token)


def decode_jwt_scopes(token):
    """
    Decode the JWT and return the scopes claim.
    """
    return configured_jwt_decode_handler(token).get('scopes', [])


def decode_jwt_is_restricted(token):
    """
    Decode the JWT and return the is_restricted claim.
    """
    return configured_jwt_decode_handler(token).get('is_restricted', False)


def decode_jwt_filters(token):
    """
    Decode the JWT, parse the filters claim, and return a
    list of (filter_type, filter_value) tuples.
    """
    return [
        jwt_filter.split(':')
        for jwt_filter in configured_jwt_decode_handler(token).get('filters', [])
    ]


def _set_token_defaults(token):
    """
    Returns an updated token that includes default values for
    fields that were introduced since the token was created
    by checking its version number.
    """
    def _verify_version(jwt_version):
        supported_version = Version(
            settings.JWT_AUTH.get('JWT_SUPPORTED_VERSION', JwtTokenVersion.default_latest_supported)
        )
        if jwt_version.major > supported_version.major:
            logger.info('Token decode failed due to unsupported JWT version number [%s]', str(jwt_version))
            raise jwt.InvalidTokenError('JWT version number [%s] is unsupported' % str(jwt_version))

    def _get_and_set_version(token):
        """
        Tokens didn't always contain a version number so we
        default to a nominal starting number.
        """
        if 'version' not in token:
            token['version'] = str(JwtTokenVersion.starting_version)

        return Version(token['version'])

    def _set_is_restricted(token):
        """
        We can safely default to False since all "restricted" tokens
        created prior to the addition of the `is_restricted` flag were
        always created as expired tokens. Expired tokens would not
        validate and so would not get this far into the decoding process.
        # TODO: ARCH-166
        """
        if 'is_restricted' not in token:
            token['is_restricted'] = False

    def _set_filters(token):
        """
        We can safely default to an empty list of filters since
        previously created tokens were either "restricted" (always
        expired) or had full access.
        # TODO: ARCH-166
        """
        if 'filters' not in token:
            token['filters'] = []

    token_version = _get_and_set_version(token)
    _verify_version(token_version)
    _set_is_restricted(token)
    _set_filters(token)
    return token


def _verify_jwt_signature(token, jwt_issuer):
    key_set = _get_signing_jwk_key_set(jwt_issuer)

    try:
        _ = JWS().verify_compact(token, key_set)
    except Exception as token_error:
        logger.exception('Token verification failed.')
        exc_info = sys.exc_info()
        raise jwt.InvalidTokenError(exc_info[2]) from token_error


def _decode_and_verify_token(token, jwt_issuer):
    options = {
        'require': ["exp", "iat"],

        'verify_exp': api_settings.JWT_VERIFY_EXPIRATION,
        'verify_aud': settings.JWT_AUTH.get('JWT_VERIFY_AUDIENCE', True),
        'verify_iss': False,  # TODO (ARCH-204): manually verify until issuer is configured correctly.
        'verify_signature': False,  # Verified with JWS already
    }

    decoded_token = jwt.decode(
        token,
        jwt_issuer['SECRET_KEY'],
        options=options,
        leeway=api_settings.JWT_LEEWAY,
        audience=jwt_issuer['AUDIENCE'],
        issuer=jwt_issuer['ISSUER'],
        algorithms=[api_settings.JWT_ALGORITHM],
    )

    # TODO (ARCH-204): verify issuer manually until it is properly configured.
    token_issuer = decoded_token.get('iss')
    issuer_matched = any(issuer['ISSUER'] == token_issuer for issuer in get_jwt_issuers())
    if not issuer_matched:
        logger.info('Token decode failed due to mismatched issuer [%s]', token_issuer)
        raise jwt.InvalidTokenError('%s is not a valid issuer.' % token_issuer)

    return decoded_token


def _get_signing_jwk_key_set(jwt_issuer):
    """
    Returns a JWK Keyset containing all active keys that are configured
    for verifying signatures.
    """
    key_set = KEYS()

    # asymmetric keys
    signing_jwk_set = settings.JWT_AUTH.get('JWT_PUBLIC_SIGNING_JWK_SET')
    if signing_jwk_set:
        key_set.load_jwks(signing_jwk_set)

    # symmetric key
    key_set.add({'key': jwt_issuer['SECRET_KEY'], 'kty': 'oct'})

    return key_set
