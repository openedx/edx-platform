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
