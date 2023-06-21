"""
Helps for building discussions URLs
"""
from typing import Optional
from urllib.parse import urlencode

from django.conf import settings
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


def _get_url_with_view_query_params(path: str, view: Optional[str] = None) -> str:
    """
    Helper function to build url if a url is configured

    Args:
        path (str): The path in the discussions MFE
        view (str): which view to generate url for

    Returns:
        (str) URL link for MFE

    """
    discussion_microfontend_url = configuration_helpers.get_value(
        'DISCUSSIONS_MICROFRONTEND_URL',
        settings.DISCUSSIONS_MICROFRONTEND_URL,
    )
    if not discussion_microfontend_url:
        return ''
    url = f"{discussion_microfontend_url}/{path}"

    query_params = {}
    if view == "in_context":
        query_params.update({'inContext': True})

    if query_params:
        url = f"{url}?{urlencode(query_params)}"

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
