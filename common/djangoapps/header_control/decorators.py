"""
Middleware decorator for removing headers.
"""

from functools import wraps
from header_control import remove_headers_from_response, force_header_for_response


def remove_headers(*headers):
    """
    Decorator that removes specific headers from the response.
    Usage:
        @remove_headers("Vary")
        def myview(request):
            ...

    The HeaderControlMiddleware must be used and placed as closely as possible to the top
    of the middleware chain, ideally after any caching middleware but before everything else.

    This decorator is not safe for multiple uses: each call will overwrite any previously set values.
    """
    def _decorator(func):
        """
        Decorates the given function.
        """
        @wraps(func)
        def _inner(*args, **kwargs):
            """
            Alters the response.
            """
            response = func(*args, **kwargs)
            remove_headers_from_response(response, *headers)
            return response

        return _inner

    return _decorator


def force_header(header, value):
    """
    Decorator that forces a header in the response to have a specific value.
    Usage:
        @force_header("Vary", "Origin")
        def myview(request):
            ...

    The HeaderControlMiddleware must be used and placed as closely as possible to the top
    of the middleware chain, ideally after any caching middleware but before everything else.

    This decorator is not safe for multiple uses: each call will overwrite any previously set values.
    """
    def _decorator(func):
        """
        Decorates the given function.
        """
        @wraps(func)
        def _inner(*args, **kwargs):
            """
            Alters the response.
            """
            response = func(*args, **kwargs)
            force_header_for_response(response, header, value)
            return response

        return _inner

    return _decorator
