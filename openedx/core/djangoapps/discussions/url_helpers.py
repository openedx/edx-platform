"""
Helps for building discussions URLs
"""
from typing import Optional

from django.conf import settings
from opaque_keys.edx.keys import CourseKey


def _get_url_with_view_query_params(path: str, view: Optional[str] = None) -> str:
    """
    Helper function to build url if a url is configured

    Args:
        path (str): The path in the discussions MFE
        view (str): which view to generate url for

    Returns:
        (str) URL link for MFE

    """
    if settings.DISCUSSIONS_MICROFRONTEND_URL is None:
        return ''
    url = f"{settings.DISCUSSIONS_MICROFRONTEND_URL}/{path}"
    if view == "in_context":
        url = f"{url}?inContext"
    return url


def get_discussions_mfe_url(course_key: CourseKey, view: Optional[str] = None) -> str:
    """
    Returns the url for discussions for the specified course in the discussions MFE.

    Args:
        course_key (CourseKey): course key of course for which to get url
        view (str): which view to generate url for

    Returns:
        (str) URL link for MFE. Empty if the base url isn't configured
    """
    return _get_url_with_view_query_params(f"{course_key}/", view)


def get_discussions_mfe_topic_url(course_key: CourseKey, topic_id: str, view: Optional[str] = None) -> str:
    """
    Returns the url for discussions for the specified course and topic in the discussions MFE.

    Args:
        course_key (CourseKey): course key of course for which to get url
        topic_id (str): topic id for topic to get url for
        view (str): which view to generate url for

    Returns:
        (str) URL link for MFE. Empty if the base url isn't configured
    """
    return _get_url_with_view_query_params(f"{course_key}/topics/{topic_id}", view)
