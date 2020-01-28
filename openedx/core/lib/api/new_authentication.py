""" Common Authentication Handlers used across projects. """


import logging

import django.utils.timezone
from django.conf import settings
from oauth2_provider import models as dot_models
from provider.oauth2 import models as dop_models
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from edx_django_utils.monitoring import set_custom_metric


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
    www_authenticate_realm = 'api'
    allow_query_params_token = settings.DEBUG
    allow_inactive_users = False

    def authenticate(self, request):
        """
        Returns two-tuple of (user, token) if access token authentication
        succeeds, raises an AuthenticationFailed (HTTP 401) if authentication
        fails or None if the user did not try to authenticate using an access
        token.
        """

        set_custom_metric("OAuth2AuthenticationCalled", True)
        auth = get_authorization_header(request).split()

        if len(auth) == 1:
            raise AuthenticationFailed({
                'error_code': OAUTH2_TOKEN_ERROR_NOT_PROVIDED,
                'developer_message': 'Invalid token header. No credentials provided.'})
        elif len(auth) > 2:
            raise AuthenticationFailed({
                'error_code': OAUTH2_TOKEN_ERROR_MALFORMED,
                'developer_message': 'Invalid token header. Token string should not contain spaces.'})

        if auth and auth[0].lower() == b'bearer':
            access_token = auth[1].decode('utf8')
        elif 'access_token' in request.POST:
            access_token = request.POST['access_token']
        elif 'access_token' in request.GET and self.allow_query_params_token:
            access_token = request.GET['access_token']
        else:
            logger.warning("auth is empty")
            return None
        user, token = self.authenticate_credentials(access_token)
        if not self.allow_inactive_users:
            if not user.is_active:
                msg = 'User inactive or deleted: %s' % user.get_username()
                raise AuthenticationFailed(msg)

        set_custom_metric("OAuth2AuthenticationSuccess", True)

        return user, token

    def authenticate_credentials(self, access_token):
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
            return token.user, token

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

    def authenticate_header(self, request):
        """
        Bearer is the only finalized type currently
        Check details on the `OAuth2Authentication.authenticate` method
        """
        return 'Bearer realm="%s"' % self.www_authenticate_realm


class OAuth2AuthenticationAllowInactiveUser(OAuth2Authentication):
    """
    This is a temporary workaround while the is_active field on the user is coupled
    with whether or not the user has verified ownership of their claimed email address.
    Once is_active is decoupled from verified_email, we will no longer need this
    class override.

    But until then, this authentication class ensures that the user is logged in,
    but does not require that their account "is_active".

    This class can be used for an OAuth2-accessible endpoint that allows users to access
    that endpoint without having their email verified.  For example, this is used
    for mobile endpoints.
    """

    allow_inactive_users = True
