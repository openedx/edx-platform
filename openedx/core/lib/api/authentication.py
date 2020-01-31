""" Common Authentication Handlers used across projects. """


import logging

import django.utils.timezone
from oauth2_provider import models as dot_models
from provider.oauth2 import models as dop_models
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_oauth.authentication import OAuth2Authentication as OAuth2AuthenticationDeprecatedBase
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from edx_django_utils.monitoring import set_custom_metric

OAUTH2_TOKEN_ERROR = 'token_error'
OAUTH2_TOKEN_ERROR_EXPIRED = 'token_expired'
OAUTH2_TOKEN_ERROR_MALFORMED = 'token_malformed'
OAUTH2_TOKEN_ERROR_NONEXISTENT = 'token_nonexistent'
OAUTH2_TOKEN_ERROR_NOT_PROVIDED = 'token_not_provided'
OAUTH2_USER_NOT_ACTIVE_ERROR = 'user_not_active'


logger = logging.getLogger(__name__)


class OAuth2AuthenticationDeprecated(OAuth2AuthenticationDeprecatedBase):
    """
    This child class was added to add new_relic metrics to OAuth2Authentication. This should be very temporary.
    """

    def authenticate(self, request):
        """
        Returns two-tuple of (user, token) if access token authentication
        succeeds, None if the user did not try to authenticate using an access
        token, or raises an AuthenticationFailed (HTTP 401) if authentication
        fails.
        """
        set_custom_metric("OAuth2AuthenticationDeprecated", "Failed")
        output = super(OAuth2AuthenticationDeprecated, self).authenticate(request)
        if output is None:
            set_custom_metric("OAuth2AuthenticationDeprecated", "None")
        else:
            set_custom_metric("OAuth2AuthenticationDeprecated", "Success")
        return output


class OAuth2AuthenticationAllowInactiveUser(OAuth2AuthenticationDeprecated):
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

    def authenticate(self, request):
        """
        Returns two-tuple of (user, token) if access token authentication
        succeeds, raises an AuthenticationFailed (HTTP 401) if authentication
        fails or None if the user did not try to authenticate using an access
        token.
        """

        try:
            return super(OAuth2AuthenticationAllowInactiveUser, self).authenticate(request)
        except AuthenticationFailed as exc:
            if isinstance(exc.detail, dict):
                developer_message = exc.detail['developer_message']
                error_code = exc.detail['error_code']
            else:
                developer_message = exc.detail
                if 'No credentials provided' in developer_message:
                    error_code = OAUTH2_TOKEN_ERROR_NOT_PROVIDED
                elif 'Token string should not contain spaces' in developer_message:
                    error_code = OAUTH2_TOKEN_ERROR_MALFORMED
                else:
                    error_code = OAUTH2_TOKEN_ERROR
            raise AuthenticationFailed({
                u'error_code': error_code,
                u'developer_message': developer_message
            })

    def authenticate_credentials(self, request, access_token):
        """
        Authenticate the request, given the access token.
        Overrides base class implementation to discard failure if user is
        inactive.
        """

        token = self.get_access_token(access_token)
        if not token:
            raise AuthenticationFailed({
                u'error_code': OAUTH2_TOKEN_ERROR_NONEXISTENT,
                u'developer_message': u'The provided access token does not match any valid tokens.'
            })
        elif token.expires < django.utils.timezone.now():
            raise AuthenticationFailed({
                u'error_code': OAUTH2_TOKEN_ERROR_EXPIRED,
                u'developer_message': u'The provided access token has expired and is no longer valid.',
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


class OAuth2Authentication(BaseAuthentication):
    """
    OAuth 2 authentication backend using either `django-oauth2-provider` or 'django-oauth-toolkit'
    """

    www_authenticate_realm = 'api'

    def authenticate(self, request):
        """
        Returns tuple (user, token) if access token authentication  succeeds,
        returns None if the user did not try to authenticate using an access
        token, or raises an AuthenticationFailed (HTTP 401) if authentication
        fails.
        """

        set_custom_metric("OAuth2Authentication", "Failed")  # default value
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
            set_custom_metric('OAuth2Authentication_token_location', 'bearer-in-header')
        elif 'access_token' in request.POST:
            access_token = request.POST['access_token']
            set_custom_metric('OAuth2Authentication_token_location', 'post-token')
        else:
            set_custom_metric("OAuth2Authentication", "None")
            return None

        user, token = self.authenticate_credentials(access_token)

        set_custom_metric("OAuth2Authentication", "Success")

        return user, token

    def authenticate_credentials(self, access_token):
        """
        Authenticate the request, given the access token.

        Overrides base class implementation to discard failure if user is
        inactive.
        """

        try:
            token = self.get_access_token(access_token)
        except AuthenticationFailed as exc:
            raise AuthenticationFailed({
                u'error_code': OAUTH2_TOKEN_ERROR,
                u'developer_message': exc.detail
            })

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
            # Check to make sure the users have activated their account(by confirming their email)
            if not user.is_active:
                set_custom_metric("OAuth2Authentication_user_active", False)
                msg = 'User inactive or deleted: %s' % user.get_username()
                raise AuthenticationFailed({
                    'error_code': OAUTH2_USER_NOT_ACTIVE_ERROR,
                    'developer_message': msg})
            else:
                set_custom_metric("OAuth2Authentication_user_active", True)

            return user, token

    def get_access_token(self, access_token):
        """
        Return a valid access token that exists in one of our OAuth2 libraries,
        or None if no matching token is found.
        """
        dot_token_return = self._get_dot_token(access_token)
        if dot_token_return is not None:
            set_custom_metric('OAuth2Authentication_token_type', 'dot')
            return dot_token_return
        dop_token_return = self._get_dop_token(access_token)
        if dop_token_return is not None:
            set_custom_metric('OAuth2Authentication_token_type', 'dop')
            return dop_token_return
        set_custom_metric('OAuth2Authentication_token_type', 'None')
        return None

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
