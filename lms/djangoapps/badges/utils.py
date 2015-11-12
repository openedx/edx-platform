"""
Utility functions used by the badging app.
"""
from django.conf import settings


def site_prefix():
    """
    Get the prefix for the site URL-- protocol and server name.
    """
    scheme = u"https" if settings.HTTPS == "on" else u"http"
    return u'{}://{}'.format(scheme, settings.SITE_NAME)


def requires_badges_enabled(function):
    """
    Decorator that bails a function out early if badges aren't enabled.
    """
    def wrapped(*args, **kwargs):
        """
        Wrapped function which bails out early if bagdes aren't enabled.
        """
        if not settings.FEATURES.get('ENABLE_OPENBADGES', False):
            return
        return function(*args, **kwargs)
    return wrapped
