""" Common Authentication Handlers used across projects. """


import logging

import django.utils.timezone
from oauth2_provider import models as dot_models
from provider.oauth2 import models as dop_models
from rest_framework.exceptions import AuthenticationFailed
from openedx.core.lib.api.temp_authentication import OAuth2Authentication


OAUTH2_TOKEN_ERROR = u'token_error'
OAUTH2_TOKEN_ERROR_EXPIRED = u'token_expired'
OAUTH2_TOKEN_ERROR_MALFORMED = u'token_malformed'
OAUTH2_TOKEN_ERROR_NONEXISTENT = u'token_nonexistent'
OAUTH2_TOKEN_ERROR_NOT_PROVIDED = u'token_not_provided'


log = logging.getLogger(__name__)


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