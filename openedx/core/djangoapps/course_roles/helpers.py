"""
Helpers for the course roles app.
"""

from openedx.core.lib.cache_utils import request_cached


@request_cached()
def permission_check():
    """
    Check if a user has a permission.
    """
    pass
