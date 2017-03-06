"""
This module aims to give a little more fine-tuned control of caching and cache
invalidation. Import these instead of django.core.cache.

Note that 'default' is being preserved for user session caching, which we're
not migrating so as not to inconvenience users by logging them all out.
"""
import urllib
from functools import wraps

from django.conf import settings
from django.core import cache


# If we can't find a 'general' CACHE defined in settings.py, we simply fall back
# to returning the default cache. This will happen with dev machines.
from django.utils.translation import get_language

try:
    cache = cache.caches['general']         # pylint: disable=invalid-name
except Exception:
    cache = cache.cache


def cache_if_anonymous(*get_parameters):
    """Cache a page for anonymous users.

    Many of the pages in edX are identical when the user is not logged
    in, but should not be cached when the user is logged in (because
    of the navigation bar at the top with the username).

    The django middleware cache does not handle this correctly, because
    we access the session to put the csrf token in the header. This adds
    the cookie to the vary header, and so every page is cached seperately
    for each user (because each user has a different csrf token).

    Optionally, provide a series of GET parameters as arguments to cache
    pages with these GET parameters separately.

    Note that this decorator should only be used on views that do not
    contain the csrftoken within the html. The csrf token can be included
    in the header by ordering the decorators as such:

    @ensure_csrftoken
    @cache_if_anonymous()
    def myView(request):
    """
    def decorator(view_func):
        """The outer wrapper, used to allow the decorator to take optional arguments."""
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            """The inner wrapper, which wraps the view function."""
            # Certificate authentication uses anonymous pages,
            # specifically the branding index, to do authentication.
            # If that page is cached the authentication doesn't
            # happen, so we disable the cache when that feature is enabled.
            if (
                not request.user.is_authenticated() and
                not settings.FEATURES['AUTH_USE_CERTIFICATES']
            ):
                # Use the cache. The same view accessed through different domain names may
                # return different things, so include the domain name in the key.
                domain = str(request.META.get('HTTP_HOST')) + '.'
                cache_key = domain + "cache_if_anonymous." + get_language() + '.' + request.path

                # Include the values of GET parameters in the cache key.
                for get_parameter in get_parameters:
                    parameter_value = request.GET.get(get_parameter)
                    if parameter_value is not None:
                        # urlencode expects data to be of type str, and doesn't deal well with Unicode data
                        # since it doesn't provide a way to specify an encoding.
                        cache_key = cache_key + '.' + urllib.urlencode({
                            get_parameter: unicode(parameter_value).encode('utf-8')
                        })

                response = cache.get(cache_key)  # pylint: disable=maybe-no-member
                if not response:
                    response = view_func(request, *args, **kwargs)
                    cache.set(cache_key, response, 60 * 3)  # pylint: disable=maybe-no-member

                return response

            else:
                # Don't use the cache.
                return view_func(request, *args, **kwargs)

        return wrapper
    return decorator
