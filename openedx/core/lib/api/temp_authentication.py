""" Common Authentication Handlers used across projects. """


import logging

import django.utils.timezone
from oauth2_provider import models as dot_models
from provider.oauth2 import models as dop_models
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authentication import BaseAuthentication, get_authorization_header


OAUTH2_TOKEN_ERROR = 'token_error'
OAUTH2_TOKEN_ERROR_EXPIRED = 'token_expired'
OAUTH2_TOKEN_ERROR_MALFORMED = 'token_malformed'
OAUTH2_TOKEN_ERROR_NONEXISTENT = 'token_nonexistent'
OAUTH2_TOKEN_ERROR_NOT_PROVIDED = 'token_not_provided'


logger = logging.getLogger(__name__)


class OAuth2Authentication(BaseAuthentication):
    """
    This is created to be a drop in replacement for django-rest-framework-oauth oauth2Authentication class.
    This is based on NOAuth2AuthenticationAllowINactiveUsers
    """

    def authenticate(self, request):
        """
        Returns two-tuple of (user, token) if access token authentication
        succeeds, raises an AuthenticationFailed (HTTP 401) if authentication
        fails or None if the user did not try to authenticate using an access
        token.
        """

        auth = get_authorization_header(request).split()
        if not auth or auth[0].lower() != b'bearer':
            logger.warning("auth is empty")
            return None

        if len(auth) == 1:
            raise AuthenticationFailed({
                'error_code': OAUTH2_TOKEN_ERROR_NOT_PROVIDED,
                'developer_message': 'Invalid token header. No credentials provided.'})
        elif len(auth) > 2:
            raise AuthenticationFailed({
                'error_code': OAUTH2_TOKEN_ERROR_MALFORMED,
                'developer_message': 'Invalid token header. Token string should not contain spaces.'})
        return self.authenticate_credentials(request, auth[1].decode('utf8'))

    def authenticate_credentials(self, request, access_token):
        """
        Authenticate the request, given the access token.

        Overrides base class implementation to discard failure if user is
        inactive.
        """

        token = self.get_access_token(access_token)
        if not token:
            raise AuthenticationFailed({
                'error_code': OAUTH2_TOKEN_ERROR_NONEXISTENT,
                'developer_message': 'The provided access token does not match any valid tokens.'
            })
        elif token.expires < django.utils.timezone.now():
            raise AuthenticationFailed({
                'error_code': OAUTH2_TOKEN_ERROR_EXPIRED,
                'developer_message': 'The provided access token has expired and is no longer valid.',
            })
        else:
            user = token.user
            if not user.is_active:
                msg = 'User inactive or deleted: %s' % user.get_username()
                raise AuthenticationFailed(msg)
            return user, token

    def get_access_token(self, access_token):
        """
        Return a valid access token that exists in one of our OAuth2 libraries,
        or None if no matching token is found.
        """
        return self._get_dot_token(access_token) or self._get_dop_token(access_token)

    def _get_dop_token(self, access_token):
        """
        Return a valid access token stored by django-oauth2-provider (DOP), or
        None if no matching token is found.
        """
        token_query = dop_models.AccessToken.objects.select_related('user')
        return token_query.filter(token=access_token).first()

    def _get_dot_token(self, access_token):
        """
        Return a valid access token stored by django-oauth-toolkit (DOT), or
        None if no matching token is found.
        """
        token_query = dot_models.AccessToken.objects.select_related('user')
        return token_query.filter(token=access_token).first()
