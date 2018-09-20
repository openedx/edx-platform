"""Utilities for working with ID tokens."""
import json
from time import time

from django.conf import settings
from jwkest import jwk
from jwkest.jws import JWS

from edx_django_utils.monitoring import set_custom_metric
from openedx.core.djangoapps.oauth_dispatch.toggles import ENFORCE_JWT_SCOPES
from student.models import UserProfile, anonymous_id_for_user


def create_api_client_jwt(user, secret=None, aud=None, additional_claims=None):
    """
    To create JWTs for API clients that are making REST API calls to other edX services.

    Arguments:
        user (User): User for which to generate the JWT.

    Deprecated Arguments (to be removed):
        secret (string): Overrides configured JWT secret (signing) key.
        aud (string): Optional. Overrides configured JWT audience claim.
        additional_claims (dict): Optional. Additional claims to include in the token.
    """
    expires_in = settings.OAUTH_ID_TOKEN_EXPIRATION
    return _create_token(
        user,
        expires_in=expires_in,
        aud=aud,
        additional_claims=additional_claims,
        secret=secret,
    )


def create_app_access_jwt(user, scopes, expires_in, is_restricted, filters):
    """
    To create JWTs for OAuth applications needing access to various edX services.

    Arguments:
        user (User): User for which to generate the JWT.
        scopes (list): Scopes that limit access to the token bearer and
            controls which optional claims are included in the token.
        expires_in (int): Time to token expiry, specified in seconds.
        is_restricted (Boolean): Whether the client to whom the JWT is issued is restricted.
        filters (list): Optional. Filters to include in the JWT.
    """
    # If JWT scope enforcement is enabled, we need to sign tokens
    # given to restricted applications with a key that
    # other IDAs do not have access to. This prevents restricted
    # applications from getting access to API endpoints available
    # on other IDAs which have not yet been protected with the
    # scope-related DRF permission classes. Once all endpoints have
    # been protected, we can enable all IDAs to use the same new
    # (asymmetric) key.
    # TODO: ARCH-162
    use_asymmetric_key = ENFORCE_JWT_SCOPES.is_enabled() and is_restricted
    return _create_token(
        user,
        scopes,
        expires_in=expires_in,
        is_restricted=is_restricted,
        filters=filters,
        asymmetric=use_asymmetric_key,
    )


def create_user_login_jwt(user, expires_in):
    """
    To create JWTs for end users upon login.

    Arguments:
        user (User): User for which to generate the JWT.
        expires_in (int): Time to token expiry, specified in seconds.
    """
    return _create_token(
        user,
        expires_in=expires_in,
        asymmetric=True,
    )


def _create_token(
    user,
    scopes=None,
    expires_in=None,
    is_restricted=False,
    filters=None,
    aud=None,
    additional_claims=None,
    asymmetric=False,
    secret=None,
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

    Deprecated Arguments (to be removed):
        aud (string): Optional. Overrides configured JWT audience claim.
        additional_claims (dict): Optional. Additional claims to include in the token.
        asymmetric (Boolean): Whether the JWT should be signed with this app's private key.
        secret (string): Overrides configured JWT secret (signing) key.
    """
    scopes = scopes or ['email', 'profile']
    now = int(time())
    expires_in = expires_in or settings.JWT_AUTH['JWT_EXPIRATION']
    set_custom_metric('jwt_expires_in', expires_in)

    payload = {
        # TODO Consider getting rid of this claim since we don't use it.
        'aud': aud if aud else settings.JWT_AUTH['JWT_AUDIENCE'],
        'exp': now + expires_in,
        'iat': now,
        'iss': settings.JWT_AUTH['JWT_ISSUER'],
        'preferred_username': user.username,
        'scopes': scopes,
        'version': settings.JWT_AUTH['JWT_SUPPORTED_VERSION'],
        'sub': anonymous_id_for_user(user, None),
    }

    claims = additional_claims or {}
    claims.update({
        'filters': filters or [],
        'is_restricted': is_restricted,
    })
    payload.update(claims)

    for scope in scopes:
        handler = _claim_handlers().get(scope)
        if handler:
            handler(payload, user)

    return _encode(payload, asymmetric, secret)


def _claim_handlers():
    """Returns a dictionary mapping scopes to methods that will add claims to the JWT payload."""

    return {
        'email': _attach_email_claim,
        'profile': _attach_profile_claim
    }


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
    })


def _encode(payload, asymmetric, secret):
    """Encode the provided payload."""
    set_custom_metric('jwt_asymmetric', asymmetric)
    keys = jwk.KEYS()

    if asymmetric:
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
