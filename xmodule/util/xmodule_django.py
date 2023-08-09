"""
Exposes Django utilities for consumption in the xmodule library
"""
# NOTE: we are importing this method so that any module that imports us has access to get_current_request
from crum import get_current_request


def get_current_request_hostname():
    """
    This method will return the hostname that was used in the current Django request
    """
    hostname = None
    request = get_current_request()
    if request:
        hostname = request.META.get('HTTP_HOST')

    return hostname
