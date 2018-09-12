""" OAuth related Python apis. """
from oauth2_provider.models import AccessToken as dot_access_token
from oauth2_provider.models import RefreshToken as dot_refresh_token
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
