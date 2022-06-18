"""
JWT Authentication cookie utilities.
"""

from django.conf import settings

from edx_rest_framework_extensions.auth.jwt.decoder import configured_jwt_decode_handler


def jwt_cookie_name():
    return settings.JWT_AUTH.get('JWT_AUTH_COOKIE') or 'edx-jwt-cookie'


def jwt_cookie_header_payload_name():
    return settings.JWT_AUTH.get('JWT_AUTH_COOKIE_HEADER_PAYLOAD') or 'edx-jwt-cookie-header-payload'


def jwt_cookie_signature_name():
    return settings.JWT_AUTH.get('JWT_AUTH_COOKIE_SIGNATURE') or 'edx-jwt-cookie-signature'


def get_decoded_jwt(request):
    """
    Grab jwt from jwt cookie in request if possible.

    Returns a decoded jwt dict if it can be found.
    Returns None if the jwt is not found.
    """
    jwt_cookie = request.COOKIES.get(jwt_cookie_name(), None)

    if not jwt_cookie:
        return None
    return configured_jwt_decode_handler(jwt_cookie)
