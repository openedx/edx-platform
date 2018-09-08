"""
The middleware for the edx-platform version of the RequestCache has been
removed in favor of the RequestCache found in edx-django-utils.

TODO: This file still contains request cache related decorators that
should be moved out of this middleware file.
"""
from django.utils.encoding import force_text
from edx_django_utils.cache import RequestCache


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
            their own sub-cache by, for example, calling RequestCache(namespace=NAMESPACE).clear() for their own
            namespace.
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
            request_cache = RequestCache(namespace)
            cache_key = _func_call_cache_key(f, *args, **kwargs)

            cached_response = request_cache.get_cached_response(cache_key)
            if cached_response.is_found:
                return cached_response.value

            result = f(*args, **kwargs)
            request_cache.set(cache_key, result)
            return result

        return inner_wrapper
    return outer_wrapper


def _func_call_cache_key(func, *args, **kwargs):
    """
    Returns a cache key based on the function's module
    the function's name, and a stringified list of arguments
    and a query string-style stringified list of keyword arguments.
    """
    converted_args = map(force_text, args)
    converted_kwargs = map(force_text, reduce(list.__add__, map(list, sorted(kwargs.iteritems())), []))
    cache_keys = [func.__module__, func.func_name] + converted_args + converted_kwargs
    return u'.'.join(cache_keys)
