"""
This module aims to give a little more fine-tuned control of caching and cache
invalidation. Import these instead of django.core.cache.

Note that 'default' is being preserved for user session caching, which we're
not migrating so as not to inconvenience users by logging them all out.
"""
from functools import wraps

from django.core import cache


# If we can't find a 'general' CACHE defined in settings.py, we simply fall back
# to returning the default cache. This will happen with dev machines.
from django.utils.translation import get_language

try:
    cache = cache.get_cache('general')
except Exception:
    cache = cache.cache


def cache_if_anonymous(view_func):
    """
    Many of the pages in edX are identical when the user is not logged
    in, but should not be cached when the user is logged in (because
    of the navigation bar at the top with the username).

    The django middleware cache does not handle this correctly, because
    we access the session to put the csrf token in the header. This adds
    the cookie to the vary header, and so every page is cached seperately
    for each user (because each user has a different csrf token).

    Note that this decorator should only be used on views that do not
    contain the csrftoken within the html. The csrf token can be included
    in the header by ordering the decorators as such:

    @ensure_csrftoken
    @cache_if_anonymous
    def myView(request):
    """

    @wraps(view_func)
    def _decorated(request, *args, **kwargs):
        if not request.user.is_authenticated():
            #Use the cache
            # same view accessed through different domain names may
            # return different things, so include the domain name in the key.
            domain = str(request.META.get('HTTP_HOST')) + '.'
            cache_key = domain + "cache_if_anonymous." + get_language() + '.' + request.path
            response = cache.get(cache_key)
            if not response:
                response = view_func(request, *args, **kwargs)
                cache.set(cache_key, response, 60 * 3)

            return response

        else:
            #Don't use the cache
            return view_func(request, *args, **kwargs)

    return _decorated
