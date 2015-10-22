"""
Common helpers methods for django apps.
"""

import logging

from provider.oauth2.models import AccessToken, Client
from provider.utils import now

from django.core.exceptions import ImproperlyConfigured


log = logging.getLogger(__name__)


def get_id_token(user, client_name):
    """Generates a JWT ID-Token, using or creating user's OAuth access token.

    Arguments:
        user (User Object): User for which we need to get JWT ID-Token
        client_name (unicode): Name of the OAuth2 Client

    Returns:
        String containing the signed JWT value or raise the exception
        'ImproperlyConfigured'
    """
    # TODO: there's a circular import problem somewhere which is why we do the oidc import inside of this function.
    import oauth2_provider.oidc as oidc

    try:
        client = Client.objects.get(name=client_name)
    except Client.DoesNotExist:
        raise ImproperlyConfigured("OAuth2 Client with name '%s' is not present in the DB" % client_name)

    access_tokens = AccessToken.objects.filter(
        client=client,
        user__username=user.username,
        expires__gt=now()
    ).order_by('-expires')

    if access_tokens:
        access_token = access_tokens[0]
    else:
        access_token = AccessToken.objects.create(client=client, user=user)

    id_token = oidc.id_token(access_token)
    secret = id_token.access_token.client.client_secret
    return id_token.encode(secret)
