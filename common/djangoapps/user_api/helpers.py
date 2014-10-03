"""
Helper functions for the account/profile Python APIs.
This is NOT part of the public API.
"""
from functools import wraps
import logging

LOGGER = logging.getLogger(__name__)


def intercept_errors(api_error, ignore_errors=[]):
    """
    Function decorator that intercepts exceptions
    and translates them into API-specific errors (usually an "internal" error).

    This allows callers to gracefully handle unexpected errors from the API.

    This method will also log all errors and function arguments to make
    it easier to track down unexpected errors.

    Arguments:
        api_error (Exception): The exception to raise if an unexpected error is encountered.

    Keyword Arguments:
        ignore_errors (iterable): List of errors to ignore.  By default, intercept every error.

    Returns:
        function

    """
    def _decorator(func):
        @wraps(func)
        def _wrapped(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as ex:
                # Raise the original exception if it's in our list of "ignored" errors
                for ignored in ignore_errors:
                    if isinstance(ex, ignored):
                        raise

                # Otherwise, log the error and raise the API-specific error
                msg = (
                    u"An unexpected error occurred when calling '{func_name}' "
                    u"with arguments '{args}' and keyword arguments '{kwargs}': "
                    u"{exception}"
                ).format(
                    func_name=func.func_name,
                    args=args,
                    kwargs=kwargs,
                    exception=repr(ex)
                )
                LOGGER.exception(msg)
                raise api_error(msg)
        return _wrapped
    return _decorator
