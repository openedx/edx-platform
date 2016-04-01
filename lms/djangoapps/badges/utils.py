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
        if not badges_enabled():
            return
        return function(*args, **kwargs)
    return wrapped


def badges_enabled():
    """
    returns a boolean indicating whether or not openbadges are enabled.
    """
    return settings.FEATURES.get('ENABLE_OPENBADGES', False)


def deserialize_count_specs(text):
    """
    Takes a string in the format of:
        int,course_key
        int,course_key

    And returns a dictionary with the keys as the numbers and the values as the course keys.
    """
    specs = text.splitlines()
    specs = [line.split(',') for line in specs if line.strip()]
    return {int(num): slug.strip().lower() for num, slug in specs}
