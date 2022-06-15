"""
Helper Methods
"""

from braze.client import BrazeClient
from django.conf import settings


def _get_key(key_or_id, key_cls):
    """
    Helper method to get a course/usage key either from a string or a key_cls,
    where the key_cls (CourseKey or UsageKey) will simply be returned.
    """
    return (
        key_cls.from_string(key_or_id)
        if isinstance(key_or_id, str)
        else key_or_id
    )


def get_braze_client():
    """ Returns a Braze client. """
    braze_api_key = settings.EDX_BRAZE_API_KEY
    braze_api_url = settings.EDX_BRAZE_API_SERVER

    if not braze_api_key or not braze_api_url:
        return None

    return BrazeClient(
        api_key=braze_api_key,
        api_url=braze_api_url,
        app_id='',
    )
