"""Utilities for working with access tokens."""
import logging

from django.core.exceptions import ImproperlyConfigured
from provider.oauth2.models import AccessToken, Client
from provider.utils import now


log = logging.getLogger(__name__)


def get_id_token(user, client_name):
    """Generate a JWT using the user's OAuth2 access token.

    Constructs a JWT with the scopes from the provided access token and the corresponding claims.

    Arguments:
        user (User): User for which to generate the JWT.
        client_name (unicode): Name of the OAuth2 Client for which the token is intended.

    Returns:
        str: the JWT

    Raises:
        ImproperlyConfigured: If no OAuth2 Client with the provided name exists.
    """
    # Import oidc package here to avoid problems with circular imports
    import oauth2_provider.oidc as oidc

    try:
        client = Client.objects.get(name=client_name)
    except Client.DoesNotExist:
        raise ImproperlyConfigured('OAuth2 Client with name [%s] does not exist' % client_name)

    access_token = AccessToken.objects.filter(
        client=client,
        user__username=user.username,
        expires__gt=now()
    ).order_by('-expires').first()

    if not access_token:
        access_token = AccessToken.objects.create(client=client, user=user)

    id_token = oidc.id_token(access_token)
    secret = id_token.access_token.client.client_secret

    return id_token.encode(secret)
