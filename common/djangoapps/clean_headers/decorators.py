"""
Middleware decorator for removing headers.
"""

from functools import wraps


def clean_headers(*headers):
    """
    Decorator that removes any headers specified from the response.
    Usage:
        @clean_headers("Vary")
        def myview(request):
            ...

    The CleanHeadersMiddleware must be used and placed as closely as possible to the top
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
            response.clean_headers = headers
            return response

        return _inner

    return _decorator
