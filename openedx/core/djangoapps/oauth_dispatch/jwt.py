"""Utilities for working with ID tokens."""


import json
import logging
from time import time

from django.conf import settings
from edx_django_utils.monitoring import set_custom_attribute
from edx_rbac.utils import create_role_auth_claim_for_user
from jwkest import jwk
from jwkest.jws import JWS

from common.djangoapps.student.models import UserProfile, anonymous_id_for_user

log = logging.getLogger(__name__)


def create_jwt_for_user(user, secret=None, aud=None, additional_claims=None, scopes=None):
    """
    Returns a JWT to identify the given user.

    TODO (ARCH-204) Note the returned JWT does not have an underlying access
    token associated with it and so cannot be invalidated nor refreshed. This
    interface should be revisited when addressing authentication-related cleanup
    as part of ARCH-204.

    Arguments:
        user (User): User for which to generate the JWT.
        scopes (list): Optional. Scopes that limit access to the token bearer and
            controls which optional claims are included in the token.

    Deprecated Arguments (to be removed):
        secret (string): Overrides configured JWT secret (signing) key.
        aud (string): Optional. Overrides configured JWT audience claim.
        additional_claims (dict): Optional. Additional claims to include in the token.
    """
    expires_in = settings.OAUTH_ID_TOKEN_EXPIRATION
    return _create_jwt(
        user,
        scopes=scopes,
        expires_in=expires_in,
        aud=aud,
        additional_claims=additional_claims,
        secret=secret,
        use_asymmetric_key=False,
    )


def create_jwt_token_dict(token_dict, oauth_adapter, use_asymmetric_key=None):
    """
    Returns a JWT access token dict based on the provided access token.

    Arguments:
        token_dict (dict): An access token structure as returned from an
            underlying OAuth provider. Dict includes "access_token",
            "expires_in", "token_type", and "scope".

    Deprecated Arguments (to be removed):
        oauth_adapter (DOPAdapter|DOTAdapter): An OAuth adapter that will
            provide the given token's information.
        use_asymmetric_key (Boolean): Optional. Whether the JWT should be signed
            with this app's private key. If not provided, defaults to whether
            the OAuth client is restricted.
    """
    access_token = oauth_adapter.get_access_token(token_dict['access_token'])
    client = oauth_adapter.get_client_for_token(access_token)

    jwt_expires_in = _get_jwt_access_token_expire_seconds()
    try:
        grant_type = access_token.application.authorization_grant_type
    except Exception:  # pylint: disable=broad-except
        # TODO: Remove this broad except if proven this doesn't happen.
        grant_type = 'unknown-error'
        log.exception('Unable to get grant_type from access token.')

    # .. custom_attribute_name: create_jwt_grant_type
    # .. custom_attribute_description: The grant type of the newly created JWT.
    set_custom_attribute('create_jwt_grant_type', grant_type)

    jwt_access_token = _create_jwt(
        access_token.user,
        scopes=token_dict['scope'].split(' '),
        expires_in=jwt_expires_in,
        use_asymmetric_key=use_asymmetric_key,
        is_restricted=oauth_adapter.is_client_restricted(client),
        filters=oauth_adapter.get_authorization_filters(client),
        grant_type=grant_type,
    )

    jwt_token_dict = token_dict.copy()
    # Note: only "scope" is not overwritten at this point.
    jwt_token_dict.update({
        "access_token": jwt_access_token,
        "token_type": "JWT",
        "expires_in": jwt_expires_in,
    })
    return jwt_token_dict


def create_jwt_from_token(token_dict, oauth_adapter, use_asymmetric_key=None):
    """
    Returns a JWT created from the provided access token dict.

    Note: if you need the token dict, and not just the JWT, use
        create_jwt_token_dict instead. See its docs for more details.
    """
    jwt_token_dict = create_jwt_token_dict(token_dict, oauth_adapter, use_asymmetric_key)
    return jwt_token_dict["access_token"]


def _get_jwt_access_token_expire_seconds():
    """
    Returns the number of seconds before a JWT access token expires.

    .. setting_name: JWT_ACCESS_TOKEN_EXPIRE_SECONDS
    .. setting_default: 60 * 60
    .. setting_description: The number of seconds a JWT access token remains valid. We use this
        custom setting for JWT formatted access tokens, rather than the django-oauth-toolkit setting
        ACCESS_TOKEN_EXPIRE_SECONDS, because the JWT is non-revocable and we want it to be shorter
        lived than the legacy Bearer (opaque) access tokens, and thus to have a smaller default.
    .. setting_warning: For security purposes, 1 hour (the default) is the maximum recommended setting
        value. For tighter security, you can use a shorter amount of time.
    """
    return getattr(settings, 'JWT_ACCESS_TOKEN_EXPIRE_SECONDS', 60 * 60)


def _create_jwt(
    user,
    scopes=None,
    expires_in=None,
    is_restricted=False,
    filters=None,
    aud=None,
    additional_claims=None,
    use_asymmetric_key=None,
    secret=None,
    grant_type=None,
):
    """
    Returns an encoded JWT (string).

    Arguments:
        user (User): User for which to generate the JWT.
        scopes (list): Optional. Scopes that limit access to the token bearer and
            controls which optional claims are included in the token.
            Defaults to ['email', 'profile'].
        expires_in (int): Optional. Overrides time to token expiry, specified in seconds.
        filters (list): Optional. Filters to include in the JWT.
        is_restricted (Boolean): Whether the client to whom the JWT is issued is restricted.
        grant_type (str): grant type of the new JWT token.

    Deprecated Arguments (to be removed):
        aud (string): Optional. Overrides configured JWT audience claim.
        additional_claims (dict): Optional. Additional claims to include in the token.
        use_asymmetric_key (Boolean): Optional. Whether the JWT should be signed
            with this app's private key. If not provided, defaults to whether
            the OAuth client is restricted.
        secret (string): Overrides configured JWT secret (signing) key.
    """
    use_asymmetric_key = _get_use_asymmetric_key_value(is_restricted, use_asymmetric_key)
    # Default scopes should only contain non-privileged data.
    # Do not be misled by the fact that `email` and `profile` are default scopes. They
    # were included for legacy compatibility, even though they contain privileged data.
    scopes = scopes or ['email', 'profile']
    iat, exp = _compute_time_fields(expires_in)

    payload = {
        # TODO (ARCH-204) Consider getting rid of the 'aud' claim since we don't use it.
        'aud': aud if aud else settings.JWT_AUTH['JWT_AUDIENCE'],
        'exp': exp,
        'grant_type': grant_type or '',
        'iat': iat,
        'iss': settings.JWT_AUTH['JWT_ISSUER'],
        'preferred_username': user.username,
        'scopes': scopes,
        'version': settings.JWT_AUTH['JWT_SUPPORTED_VERSION'],
        'sub': anonymous_id_for_user(user, None),
        'filters': filters or [],
        'is_restricted': is_restricted,
        'email_verified': user.is_active,
    }
    payload.update(additional_claims or {})
    _update_from_additional_handlers(payload, user, scopes)
    role_claims = create_role_auth_claim_for_user(user)
    if role_claims:
        payload['roles'] = role_claims
    return _encode_and_sign(payload, use_asymmetric_key, secret)


def _get_use_asymmetric_key_value(is_restricted, use_asymmetric_key):
    """
    Returns the value to use for use_asymmetric_key.
    """
    return use_asymmetric_key or is_restricted


def _compute_time_fields(expires_in):
    """
    Returns (iat, exp) tuple to be used as time-related values in a token.
    """
    now = int(time())
    expires_in = expires_in or settings.JWT_AUTH['JWT_EXPIRATION']
    return now, now + expires_in


def _update_from_additional_handlers(payload, user, scopes):
    """
    Updates the given token payload with data from additional handlers, as
    requested by the given scopes.
    """
    _claim_handlers = {
        'user_id': _attach_user_id_claim,
        'email': _attach_email_claim,
        'profile': _attach_profile_claim,
    }
    for scope in scopes:
        handler = _claim_handlers.get(scope)
        if handler:
            handler(payload, user)


def _attach_user_id_claim(payload, user):
    """Add the user_id claim details to the JWT payload."""
    payload['user_id'] = user.id


def _attach_email_claim(payload, user):
    """Add the email claim details to the JWT payload."""
    payload['email'] = user.email


def _attach_profile_claim(payload, user):
    """Add the profile claim details to the JWT payload."""
    try:
        # Some users (e.g., service users) may not have user profiles.
        name = UserProfile.objects.get(user=user).name
    except UserProfile.DoesNotExist:
        name = None

    payload.update({
        'name': name,
        'family_name': user.last_name,
        'given_name': user.first_name,
        'administrator': user.is_staff,
        'superuser': user.is_superuser,
    })


def _encode_and_sign(payload, use_asymmetric_key, secret):
    """Encode and sign the provided payload."""
    keys = jwk.KEYS()

    if use_asymmetric_key:
        serialized_keypair = json.loads(settings.JWT_AUTH['JWT_PRIVATE_SIGNING_JWK'])
        keys.add(serialized_keypair)
        algorithm = settings.JWT_AUTH['JWT_SIGNING_ALGORITHM']
    else:
        key = secret if secret else settings.JWT_AUTH['JWT_SECRET_KEY']
        keys.add({'key': key, 'kty': 'oct'})
        algorithm = settings.JWT_AUTH['JWT_ALGORITHM']

    data = json.dumps(payload)
    jws = JWS(data, alg=algorithm)
    return jws.sign_compact(keys=keys)
