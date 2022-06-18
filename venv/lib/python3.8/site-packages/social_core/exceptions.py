class SocialAuthBaseException(ValueError):
    """Base class for pipeline exceptions."""
    pass


class WrongBackend(SocialAuthBaseException):
    def __init__(self, backend_name):
        self.backend_name = backend_name

    def __str__(self):
        return 'Incorrect authentication service "{}"'.format(
            self.backend_name
        )


class MissingBackend(WrongBackend):
    def __str__(self):
        return f'Missing backend "{self.backend_name}" entry'


class NotAllowedToDisconnect(SocialAuthBaseException):
    """User is not allowed to disconnect it's social account."""
    def __str__(self):
        return 'This account is not allowed to be disconnected.'


class AuthException(SocialAuthBaseException):
    """Auth process exception."""
    def __init__(self, backend, *args, **kwargs):
        self.backend = backend
        super().__init__(*args, **kwargs)


class AuthFailed(AuthException):
    """Auth process failed for some reason."""
    def __str__(self):
        msg = super().__str__()
        if msg == 'access_denied':
            return 'Authentication process was canceled'
        return f'Authentication failed: {msg}'


class AuthCanceled(AuthException):
    """Auth process was canceled by user."""
    def __init__(self, *args, **kwargs):
        self.response = kwargs.pop('response', None)
        super().__init__(*args, **kwargs)

    def __str__(self):
        msg = super().__str__()
        if msg:
            return f'Authentication process canceled: {msg}'
        return 'Authentication process canceled'


class AuthUnknownError(AuthException):
    """Unknown auth process error."""
    def __str__(self):
        msg = super().__str__()
        return f'An unknown error happened while authenticating {msg}'


class AuthTokenError(AuthException):
    """Auth token error."""
    def __str__(self):
        msg = super().__str__()
        return f'Token error: {msg}'


class AuthMissingParameter(AuthException):
    """Missing parameter needed to start or complete the process."""
    def __init__(self, backend, parameter, *args, **kwargs):
        self.parameter = parameter
        super().__init__(backend, *args, **kwargs)

    def __str__(self):
        return f'Missing needed parameter {self.parameter}'


class AuthStateMissing(AuthException):
    """State parameter is incorrect."""
    def __str__(self):
        return 'Session value state missing.'


class AuthStateForbidden(AuthException):
    """State parameter is incorrect."""
    def __str__(self):
        return 'Wrong state parameter given.'


class AuthAlreadyAssociated(AuthException):
    """A different user has already associated the target social account"""
    def __str__(self):
        return 'This account is already in use.'


class AuthTokenRevoked(AuthException):
    """User revoked the access_token in the provider."""
    def __str__(self):
        return 'User revoke access to the token'


class AuthForbidden(AuthException):
    """Authentication for this user is forbidden"""
    def __str__(self):
        return 'Your credentials aren\'t allowed'


class AuthUnreachableProvider(AuthException):
    """Cannot reach the provider"""
    def __str__(self):
        return 'The authentication provider could not be reached'


class InvalidEmail(AuthException):
    def __str__(self):
        return 'Email couldn\'t be validated'
