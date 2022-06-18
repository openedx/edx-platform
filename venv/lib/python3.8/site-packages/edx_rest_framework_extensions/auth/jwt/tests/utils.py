""" Utility functions for tests. """
from time import time

import jwt
from django.conf import settings


def generate_jwt(user, scopes=None, filters=None, is_restricted=None):
    """
    Generate a valid JWT for authenticated requests.
    """
    access_token = generate_latest_version_payload(
        user,
        scopes=scopes,
        filters=filters,
        is_restricted=is_restricted
    )
    return generate_jwt_token(access_token)


def generate_jwt_token(payload, signing_key=None):
    """
    Generate a valid JWT token for authenticated requests.
    """
    signing_key = signing_key or settings.JWT_AUTH['JWT_ISSUERS'][0]['SECRET_KEY']
    return jwt.encode(payload, signing_key)


def generate_latest_version_payload(user, scopes=None, filters=None, version=None,
                                    is_restricted=None):
    """
    Generate a valid JWT payload given a user and optionally scopes and filters.
    """
    payload = generate_unversioned_payload(user)
    payload.update({
        # fix this version and add newly introduced fields as the version updates.
        'version': '1.1.0',
        'filters': [],
        'is_restricted': False,
    })
    if scopes is not None:
        payload['scopes'] = scopes
    if version is not None:
        payload['version'] = version
    if filters is not None:
        payload['filters'] = filters
    if is_restricted is not None:
        payload['is_restricted'] = is_restricted
    return payload


def generate_unversioned_payload(user):
    """
    Generate an unversioned valid JWT payload given a user.
    """
    jwt_issuer_data = settings.JWT_AUTH['JWT_ISSUERS'][0]
    now = int(time())
    ttl = 600
    payload = {
        'iss': jwt_issuer_data['ISSUER'],
        'aud': jwt_issuer_data['AUDIENCE'],
        'username': user.username,
        'email': user.email,
        'iat': now,
        'exp': now + ttl,
        'scopes': [],
    }
    return payload
