"""
Custom JWT decoding function for django_rest_framework jwt package.

Adds logging to facilitate debugging of InvalidTokenErrors.  Also
requires "exp" and "iat" claims to be present - the base package
doesn't expose settings to enforce this.
"""
import logging

import jwt
from rest_framework_jwt.settings import api_settings


log = logging.getLogger(__name__)


def decode(token):
    """
    Ensure InvalidTokenErrors are logged for diagnostic purposes, before
    failing authentication.
    """

    options = {
        'verify_exp': api_settings.JWT_VERIFY_EXPIRATION,
        'require_exp': True,
        'require_iat': True,
    }

    try:
        return jwt.decode(
            token,
            api_settings.JWT_SECRET_KEY,
            api_settings.JWT_VERIFY,
            options=options,
            leeway=api_settings.JWT_LEEWAY,
            audience=api_settings.JWT_AUDIENCE,
            issuer=api_settings.JWT_ISSUER,
            algorithms=[api_settings.JWT_ALGORITHM]
        )
    except jwt.InvalidTokenError as exc:
        exc_type = u'{}.{}'.format(exc.__class__.__module__, exc.__class__.__name__)
        log.exception("raised_invalid_token: exc_type=%r, exc_detail=%r", exc_type, exc.message)
        raise
