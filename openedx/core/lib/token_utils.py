"""Utilities for working with ID tokens."""
import datetime

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import jwt
from provider.oauth2.models import Client

from student.models import UserProfile, anonymous_id_for_user


def get_id_token(user, client_name, secret_key=None):
    """Construct a JWT for use with the named client.

    The JWT is signed with the named client's secret, and includes the following claims:

        preferred_username (str): The user's username. The claim name is borrowed from edx-oauth2-provider.
        name (str): The user's full name.
        email (str): The user's email address.
        administrator (Boolean): Whether the user has staff permissions.
        iss (str): Registered claim. Identifies the principal that issued the JWT.
        exp (int): Registered claim. Identifies the expiration time on or after which
            the JWT must NOT be accepted for processing.
        iat (int): Registered claim. Identifies the time at which the JWT was issued.
        aud (str): Registered claim. Identifies the recipients that the JWT is intended for. This implementation
            uses the named client's ID.
        sub (int): Registered claim.  Identifies the user.  This implementation uses the raw user id.

    Arguments:
        user (User): User for which to generate the JWT.
        client_name (unicode): Name of the OAuth2 Client for which the token is intended.
        secret_key (str): Optional secret key for signing the JWT. Defaults to the configured client secret
            if not provided.

    Returns:
        str: the JWT

    Raises:
        ImproperlyConfigured: If no OAuth2 Client with the provided name exists.
    """
    try:
        client = Client.objects.get(name=client_name)
    except Client.DoesNotExist:
        raise ImproperlyConfigured('OAuth2 Client with name [%s] does not exist' % client_name)

    try:
        # Service users may not have user profiles.
        full_name = UserProfile.objects.get(user=user).name
    except UserProfile.DoesNotExist:
        full_name = None

    now = datetime.datetime.utcnow()
    expires_in = getattr(settings, 'OAUTH_ID_TOKEN_EXPIRATION', 30)

    payload = {
        'preferred_username': user.username,
        'name': full_name,
        'email': user.email,
        'administrator': user.is_staff,
        'iss': settings.OAUTH_OIDC_ISSUER,
        'exp': now + datetime.timedelta(seconds=expires_in),
        'iat': now,
        'aud': client.client_id,
        'sub': anonymous_id_for_user(user, None),
    }

    if secret_key is None:
        secret_key = client.client_secret

    return jwt.encode(payload, secret_key)


def get_asymmetric_token(user, client_id):
    """Construct a JWT signed with this app's private key.

    The JWT includes the following claims:

        preferred_username (str): The user's username. The claim name is borrowed from edx-oauth2-provider.
        name (str): The user's full name.
        email (str): The user's email address.
        administrator (Boolean): Whether the user has staff permissions.
        iss (str): Registered claim. Identifies the principal that issued the JWT.
        exp (int): Registered claim. Identifies the expiration time on or after which
            the JWT must NOT be accepted for processing.
        iat (int): Registered claim. Identifies the time at which the JWT was issued.
        sub (int): Registered claim.  Identifies the user.  This implementation uses the raw user id.

    Arguments:
        user (User): User for which to generate the JWT.

    Returns:
        str: the JWT

    """
    private_key = load_pem_private_key(settings.PRIVATE_RSA_KEY, None, default_backend())

    try:
        # Service users may not have user profiles.
        full_name = UserProfile.objects.get(user=user).name
    except UserProfile.DoesNotExist:
        full_name = None

    now = datetime.datetime.utcnow()
    expires_in = getattr(settings, 'OAUTH_ID_TOKEN_EXPIRATION', 30)

    payload = {
        'preferred_username': user.username,
        'name': full_name,
        'email': user.email,
        'administrator': user.is_staff,
        'iss': settings.OAUTH_OIDC_ISSUER,
        'exp': now + datetime.timedelta(seconds=expires_in),
        'iat': now,
        'aud': client_id,
        'sub': anonymous_id_for_user(user, None),
    }

    return jwt.encode(payload, private_key, algorithm='RS512')
