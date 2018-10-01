""" OAuth related Python apis. """
import json
from django.conf import settings

from edx_oauth2_provider.constants import SCOPE_VALUE_DICT
from oauthlib.oauth2.rfc6749.errors import OAuth2Error
from oauthlib.oauth2.rfc6749.tokens import BearerToken
from oauth2_provider.models import AccessToken as dot_access_token
from oauth2_provider.models import RefreshToken as dot_refresh_token
from oauth2_provider.oauth2_backends import get_oauthlib_core
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


def create_dot_access_token(request, user, client, expires_in=None, scope=None):
    """
    Create and return a new (persisted) access token, including a refresh token.
    The token is returned in the form of a Dict:
        {
            u'access_token': u'some string',
            u'refresh_token': u'another string',
            u'token_type': u'Bearer',
            u'expires_in': 36000,
            u'scope': u'default',
        },
    """
    # TODO (ARCH-204) the 'scope' argument may not really be needed by callers.

    expires_in = _get_expires_in_value(expires_in)
    token_generator = BearerToken(
        expires_in=expires_in,
        request_validator=dot_settings.OAUTH2_VALIDATOR_CLASS(),
    )
    _populate_create_access_token_request(request, user, client, scope)
    return token_generator.create_token(request, refresh_token=True)


def refresh_dot_access_token(request, client_id, refresh_token, expires_in=None):
    """
    Create and return a new (persisted) access token, given a previously created
    refresh_token, possibly returned from create_dot_access_token above.
    """
    auth_core = get_oauthlib_core()
    expires_in = _get_expires_in_value(expires_in)
    _populate_refresh_token_request(request, client_id, refresh_token)

    # Note: Unlike create_dot_access_token, we use the top-level auth library
    # code for creating the token since we want to enforce registered validations
    # (valid refresh token, valid client, etc), rather than create the token
    # ourselves directly.
    _, _, body, status = auth_core.create_token_response(request)  # returns uri, headers, body, status

    if status != 200:
        raise OAuth2Error(body)
    return json.loads(body)


def _get_expires_in_value(expires_in):
    """
    Returns the expires_in value to use for the token.
    """
    # TODO (ARCH-246) Fix expiration configuration as this does not actually
    # override the token's expiration. Rather, DOT's save_bearer_token method
    # will always use dot_settings.ACCESS_TOKEN_EXPIRE_SECONDS.
    if not expires_in:
        seconds_in_a_day = 24 * 60 * 60
        expires_in = settings.OAUTH_EXPIRE_PUBLIC_CLIENT_DAYS * seconds_in_a_day
    return expires_in


def _populate_create_access_token_request(request, user, client, scope=None):
    """
    django-oauth-toolkit expects certain non-standard attributes to
    be present on the request object.  This function modifies the
    request object to match these expectations
    """
    if scope is None:
        scope = 0
    request.user = user
    request.scopes = [SCOPE_VALUE_DICT[scope]]
    request.client = client
    request.state = None
    request.refresh_token = None
    request.extra_credentials = None
    request.grant_type = client.authorization_grant_type


def _populate_refresh_token_request(request, client_id, refresh_token):
    """
    django-oauth-toolkit expects parameters passed through the request's POST.
    """
    request.POST = dict(
        client_id=client_id,
        refresh_token=refresh_token,
        grant_type='refresh_token',
    )
