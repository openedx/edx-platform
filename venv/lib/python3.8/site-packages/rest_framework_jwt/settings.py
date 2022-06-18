# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from rest_framework.settings import APISettings

USER_SETTINGS = getattr(settings, 'JWT_AUTH', None)

DEFAULTS = {
    'JWT_SECRET_KEY': settings.SECRET_KEY,
    'JWT_GET_USER_SECRET_KEY': None,
    'JWT_PRIVATE_KEY': None,
    'JWT_PUBLIC_KEY': None,
    'JWT_ALGORITHM': 'HS256',
    'JWT_INSIST_ON_KID': False,
    'JWT_TOKEN_ID': 'include',
    'JWT_AUDIENCE': None,
    'JWT_ISSUER': None,
    'JWT_ENCODE_HANDLER':
        'rest_framework_jwt.utils.jwt_encode_payload',
    'JWT_DECODE_HANDLER':
        'rest_framework_jwt.utils.jwt_decode_token',
    'JWT_PAYLOAD_HANDLER':
        'rest_framework_jwt.utils.jwt_create_payload',
    'JWT_PAYLOAD_GET_USERNAME_HANDLER':
        'rest_framework_jwt.utils.jwt_get_username_from_payload_handler',
    'JWT_PAYLOAD_INCLUDE_USER_ID': True,
    'JWT_VERIFY': True,
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_LEEWAY': 0,
    'JWT_EXPIRATION_DELTA': datetime.timedelta(seconds=300),
    'JWT_ALLOW_REFRESH': True,
    'JWT_REFRESH_EXPIRATION_DELTA': datetime.timedelta(days=7),
    'JWT_AUTH_HEADER_PREFIX': 'Bearer',
    'JWT_RESPONSE_PAYLOAD_HANDLER':
        'rest_framework_jwt.utils.jwt_create_response_payload',
    'JWT_AUTH_COOKIE': None,
    'JWT_AUTH_COOKIE_DOMAIN': None,
    'JWT_AUTH_COOKIE_PATH': '/',
    'JWT_AUTH_COOKIE_SECURE': True,
    'JWT_AUTH_COOKIE_SAMESITE': 'Lax',
    'JWT_IMPERSONATION_COOKIE': None,
    'JWT_DELETE_STALE_BLACKLISTED_TOKENS': False,
}

# List of settings that may be in string import notation.
IMPORT_STRINGS = (
    'JWT_ENCODE_HANDLER',
    'JWT_DECODE_HANDLER',
    'JWT_PAYLOAD_HANDLER',
    'JWT_PAYLOAD_GET_USERNAME_HANDLER',
    'JWT_RESPONSE_PAYLOAD_HANDLER',
    'JWT_GET_USER_SECRET_KEY',
)

api_settings = APISettings(USER_SETTINGS, DEFAULTS, IMPORT_STRINGS)

# check if settings have valid values
if not isinstance(api_settings.JWT_EXPIRATION_DELTA, datetime.timedelta):  # pragma: no cover

    raise ImproperlyConfigured(
        '`JWT_EXPIRATION_DELTA` setting must be instance of '
        '`datetime.timedelta`')

if not isinstance(
        api_settings.JWT_REFRESH_EXPIRATION_DELTA, datetime.timedelta):  # pragma: no cover

    raise ImproperlyConfigured(
        '`JWT_REFRESH_EXPIRATION_DELTA` setting must be instance of '
        '`datetime.timedelta`')

if api_settings.JWT_TOKEN_ID not in {'off', 'include', 'require'}:
    raise ImproperlyConfigured(
        "`JWT_TOKEN_ID` setting must be 'off', 'include' or 'require'"
    )
