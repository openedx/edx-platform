"""
An implementation of a RequestCache. This cache is reset at the beginning
and end of every request.
"""
import threading

import crum
from django.utils.encoding import force_text


class _RequestCache(threading.local):
    """
    A thread-local for storing the per-request cache.
    """
    def __init__(self):
        super(_RequestCache, self).__init__()
        self.data = {}


REQUEST_CACHE = _RequestCache()


class RequestCache(object):
    @classmethod
    def get_request_cache(cls, name=None):
        """
        This method is deprecated. Please use :func:`request_cache.get_cache`.
        """
        if name is None:
            return REQUEST_CACHE
        else:
            return REQUEST_CACHE.data.setdefault(name, {})

    @classmethod
    def get_current_request(cls):
        """
        This method is deprecated. Please use :func:`request_cache.get_request`.
        """
        return crum.get_current_request()

    @classmethod
    def clear_request_cache(cls, name=None):
        """
        Empty the request cache.
        """
        if name is None:
            REQUEST_CACHE.data = {}
        elif REQUEST_CACHE.data.get(name):
            REQUEST_CACHE.data[name] = {}

    def process_request(self, request):
        self.clear_request_cache()
        return None

    def process_response(self, request, response):
        self.clear_request_cache()
        return response

    def process_exception(self, request, exception):  # pylint: disable=unused-argument
        """
        Clear the RequestCache after a failed request.
        """
        self.clear_request_cache()
        return None


def request_cached(f):
    """
    A decorator for wrapping a function and automatically handles caching its return value, as well as returning
    that cached value for subsequent calls to the same function, with the same parameters, within a given request.

    Notes:
        - we convert arguments and keyword arguments to their string form to build the cache key, so if you have
          args/kwargs that can't be converted to strings, you're gonna have a bad time (don't do it)
        - cache key cardinality depends on the args/kwargs, so if you're caching a function that takes five arguments,
          you might have deceptively low cache efficiency.  prefer function with fewer arguments.
        - we use the default request cache, not a named request cache (this shouldn't matter, but just mentioning it)
        - benchmark, benchmark, benchmark! if you never measure, how will you know you've improved? or regressed?

    Arguments:
        f (func): the function to wrap

    Returns:
        func: a wrapper function which will call the wrapped function, passing in the same args/kwargs,
              cache the value it returns, and return that cached value for subsequent calls with the
              same args/kwargs within a single request
    """
    return ns_request_cached()(f)


def ns_request_cached(namespace=None):
    """
    Same as request_cached above, except an optional namespace can be passed in to compartmentalize the cache.

    Arguments:
        namespace (string): An optional namespace to use for the cache.  Useful if the caller wants to manage
            their own sub-cache by, for example, calling RequestCache.clear_request_cache for their own namespace.
    """
    def outer_wrapper(f):
        """
        Outer wrapper that decorates the given function

        Arguments:
            f (func): the function to wrap
        """
        def inner_wrapper(*args, **kwargs):
            """
            Wrapper function to decorate with.
            """
            # Check to see if we have a result in cache.  If not, invoke our wrapped
            # function.  Cache and return the result to the caller.
            rcache = RequestCache.get_request_cache(namespace)
            rcache = rcache.data if namespace is None else rcache
            cache_key = func_call_cache_key(f, *args, **kwargs)

            if cache_key in rcache:
                return rcache.get(cache_key)
            else:
                result = f(*args, **kwargs)
                rcache[cache_key] = result
                return result

        return inner_wrapper
    return outer_wrapper


def func_call_cache_key(func, *args, **kwargs):
    """
    Returns a cache key based on the function's module
    the function's name, and a stringified list of arguments
    and a query string-style stringified list of keyword arguments.
    """
    converted_args = map(force_text, args)
    converted_kwargs = map(force_text, reduce(list.__add__, map(list, sorted(kwargs.iteritems())), []))
    cache_keys = [func.__module__, func.func_name] + converted_args + converted_kwargs
    return u'.'.join(cache_keys)
