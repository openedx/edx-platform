"""
Utilities related to caching.
"""

import functools
from xblock.core import XBlock


def memoize_in_request_cache(request_cache_attr_name=None):
    """
    Memoize a method call's results in the request_cache if there's one. Creates the cache key by
    joining the unicode of all the args with &; so, if your arg may use the default &, it may
    have false hits.

    Arguments:
        request_cache_attr_name - The name of the field or property in this method's containing
         class that stores the request_cache.
    """
    def _decorator(func):
        """Outer method decorator."""
        @functools.wraps(func)
        def _wrapper(self, *args, **kwargs):
            """
            Wraps a method to memoize results.
            """
            request_cache = getattr(self, request_cache_attr_name, None)
            if request_cache:
                cache_key = '&'.join([hashvalue(arg) for arg in args])
                if cache_key in request_cache.data.setdefault(func.__name__, {}):
                    return request_cache.data[func.__name__][cache_key]

                result = func(self, *args, **kwargs)

                request_cache.data[func.__name__][cache_key] = result
                return result
            else:
                return func(self, *args, **kwargs)
        return _wrapper
    return _decorator


def hashvalue(arg):
    """
    If arg is an xblock, use its location. otherwise just turn it into a string
    """
    if isinstance(arg, XBlock):
        return unicode(arg.location)
    else:
        return unicode(arg)
