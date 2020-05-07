import jwt
from django.conf import settings


def encode_edly_user_info_cookie(cookie_data):
    """
    Encode edly_user_info cookie data into JWT string.

    Arguments:
        cookie_data (dict): Edly user info cookie dict.

    Returns:
        string
    """
    return jwt.encode(cookie_data, settings.EDLY_COOKIE_SECRET_KEY, algorithm=settings.EDLY_JWT_ALGORITHM)

def decode_edly_user_info_cookie(encoded_cookie_data):
    """
    Decode edly_user_info cookie data from JWT string.

    Arguments:
        encoded_cookie_data (dict): Edly user info cookie JWT encoded string.

    Returns:
        dict
    """
    return jwt.decode(encoded_cookie_data, settings.EDLY_COOKIE_SECRET_KEY, algorithms=[settings.EDLY_JWT_ALGORITHM])
