# -*- coding: utf-8 -*-

from rest_framework.exceptions import AuthenticationFailed

from rest_framework_jwt.compat import gettext_lazy as _


class MissingToken(AuthenticationFailed):
    status_code = 401
    msg = _('The token is missing.')
    default_code = 'token_missing'


class InvalidAuthorizationCredentials(AuthenticationFailed):
    status_code = 401
    msg = _('Invalid Authorization header.')
    default_code = 'invalid_authorization_credentials'

