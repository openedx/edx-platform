"""
A cache that is cleared after every request.

This module requires that :class:`request_cache.middleware.RequestCache`
is installed in order to clear the cache after each request.
"""


from request_cache import middleware


def get_cache(name):
    """
    Return the request cache named ``name``.

    Arguments:
        name (str): The name of the request cache to load

    Returns: dict
    """
    return middleware.RequestCache.get_request_cache(name)


def get_request():
    """
    Return the current request.
    """
    return middleware.RequestCache.get_current_request()
