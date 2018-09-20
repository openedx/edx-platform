""" OAuth related Python apis. """
from django.conf import settings

from oauthlib.oauth2.rfc6749.tokens import BearerToken
from oauth2_provider.models import AccessToken as dot_access_token
from oauth2_provider.models import RefreshToken as dot_refresh_token
from oauth2_provider.settings import oauth2_settings as dot_settings
from provider.oauth2.models import AccessToken as dop_access_token
from provider.oauth2.models import RefreshToken as dop_refresh_token


def destroy_oauth_tokens(user):
    """
    Destroys ALL OAuth access and refresh tokens for the given user.
    """
    dop_access_token.objects.filter(user=user.id).delete()
    dop_refresh_token.objects.filter(user=user.id).delete()
    dot_access_token.objects.filter(user=user.id).delete()
    dot_refresh_token.objects.filter(user=user.id).delete()


def create_dot_access_token(request, user, client, expires_in=None):
    """
    Create and return a new (persisted) access token, including a refresh token.
    """
    # TODO (ARCH-246) Fix expiration configuration as this does not actually
    # override the token's expiration. Rather, DOT's save_bearer_token method
    # will always use dot_settings.ACCESS_TOKEN_EXPIRE_SECONDS.
    if not expires_in:
        seconds_in_a_day = 24 * 60 * 60
        expires_in = settings.OAUTH_EXPIRE_PUBLIC_CLIENT_DAYS * seconds_in_a_day

    token_generator = BearerToken(
        expires_in=expires_in,
        request_validator=dot_settings.OAUTH2_VALIDATOR_CLASS(),
    )
    _populate_create_access_token_request(request, user, client)
    return token_generator.create_token(request, refresh_token=True)


def _populate_create_access_token_request(request, user, client):
    """
    django-oauth-toolkit expects certain non-standard attributes to
    be present on the request object.  This function modifies the
    request object to match these expectations
    """
    request.user = user
    request.scopes = []
    request.client = client
    request.state = None
    request.refresh_token = None
    request.extra_credentials = None
    request.grant_type = client.authorization_grant_type
