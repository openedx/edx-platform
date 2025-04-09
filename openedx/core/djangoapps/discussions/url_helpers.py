"""
Helps for building discussions URLs
"""
from typing import Optional
from urllib.parse import urlencode

from django.conf import settings
from opaque_keys.edx.keys import CourseKey
from lms.djangoapps.mfe_config_api.utils import get_mfe_config_for_site


def _get_url_with_view_query_params(path: str, view: Optional[str] = None) -> str:
    """
    Helper function to build url if a url is configured

    Args:
        path (str): The path in the discussions MFE
        view (str): which view to generate url for

    """
    mfe_config = get_mfe_config_for_site(mfe="discussions")
    base_url = (
        mfe_config.get("DISCUSSIONS_MFE_BASE_URL")
        or mfe_config.get("DISCUSSIONS_MICROFRONTEND_URL")
        or settings.DISCUSSIONS_MICROFRONTEND_URL
    )

    if not base_url:
        return ""

    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"

    if view == "in_context":
        url = f"{url}?{urlencode({'inContext': True})}"

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
