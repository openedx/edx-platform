""" OAuth related Python apis. """


from oauth2_provider.models import AccessToken as dot_access_token
from oauth2_provider.models import RefreshToken as dot_refresh_token
from oauth2_provider.settings import oauth2_settings as dot_settings
from oauthlib.oauth2.rfc6749.tokens import BearerToken


def destroy_oauth_tokens(user):
    """
    Destroys ALL OAuth access and refresh tokens for the given user.
    """
    dot_access_token.objects.filter(user=user.id).delete()
    dot_refresh_token.objects.filter(user=user.id).delete()


def create_dot_access_token(request, user, client, expires_in=None, scopes=None):
    """
    Create and return a new (persisted) access token, including a refresh token.
    The token is returned in the form of a Dict:
        {
            u'access_token': u'some string',
            u'refresh_token': u'another string',
            u'token_type': u'Bearer',
            u'expires_in': 36000,
            u'scope': u'profile email',
        },
    """
    expires_in = _get_expires_in_value(expires_in)
    token_generator = BearerToken(
        expires_in=expires_in,
        request_validator=dot_settings.OAUTH2_VALIDATOR_CLASS(),
    )
    _populate_create_access_token_request(request, user, client, scopes)
    return token_generator.create_token(request, refresh_token=True)


def _get_expires_in_value(expires_in):
    """
    Returns the expires_in value to use for the token.
    """
    return expires_in or dot_settings.ACCESS_TOKEN_EXPIRE_SECONDS


def _populate_create_access_token_request(request, user, client, scopes):
    """
    django-oauth-toolkit expects certain non-standard attributes to
    be present on the request object.  This function modifies the
    request object to match these expectations
    """
    request.user = user
    request.client = client
    request.scopes = scopes or ''
    request.state = None
    request.refresh_token = None
    request.extra_credentials = None
    request.grant_type = client.authorization_grant_type
