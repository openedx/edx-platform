"""
Custom exceptions, that allow details to be passed as dict values (which can be
converted to JSON, like other API responses.
"""

from rest_framework import exceptions


# TODO: Override Throttled, UnsupportedMediaType, ValidationError.  These types require
# more careful handling of arguments.


class _DictAPIException(exceptions.APIException):
    """
    Intermediate class to allow exceptions to pass dict detail values.  Use by
    subclassing this along with another subclass of `exceptions.APIException`.
    """
    def __init__(self, detail):
        if isinstance(detail, dict):
            self.detail = detail
        else:
            super(_DictAPIException, self).__init__(detail)


class AuthenticationFailed(exceptions.AuthenticationFailed, _DictAPIException):
    """
    Override of DRF's AuthenticationFailed exception to allow dictionary responses.
    """
    pass


class MethodNotAllowed(exceptions.MethodNotAllowed, _DictAPIException):
    """
    Override of DRF's MethodNotAllowed exception to allow dictionary responses.
    """
    def __init__(self, method, detail=None):
        if isinstance(detail, dict):
            self.detail = detail
        else:
            super(MethodNotAllowed, self).__init__(method, detail)


class NotAcceptable(exceptions.NotAcceptable, _DictAPIException):
    """
    Override of DRF's NotAcceptable exception to allow dictionary responses.
    """

    def __init__(self, detail=None, available_renderers=None):
        self.available_renderers = available_renderers
        if isinstance(detail, dict):
            self.detail = detail
        else:
            super(NotAcceptable, self).__init__(detail, available_renderers)


class NotAuthenticated(exceptions.NotAuthenticated, _DictAPIException):
    """
    Override of DRF's NotAuthenticated exception to allow dictionary responses.
    """
    pass


class NotFound(exceptions.NotFound, _DictAPIException):
    """
    Override of DRF's NotFound exception to allow dictionary responses.
    """
    pass


class ParseError(exceptions.ParseError, _DictAPIException):
    """
    Override of DRF's ParseError exception to allow dictionary responses.
    """
    pass


class PermissionDenied(exceptions.PermissionDenied, _DictAPIException):
    """
    Override of DRF's PermissionDenied exception to allow dictionary responses.
    """
    pass
