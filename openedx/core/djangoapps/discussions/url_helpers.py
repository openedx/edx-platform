"""
Helps for building discussions URLs
"""
from django.conf import settings
from opaque_keys.edx.keys import CourseKey


def get_discussions_mfe_url(course_key: CourseKey) -> str:
    """
    Returns the url for discussions for the specified course in the discussions MFE.

    Args:
        course_key (CourseKey): course key of course for which to get url

    Returns:
        (str) URL link for MFE. Empty if the base url isn't configured
    """
    if settings.DISCUSSIONS_MICROFRONTEND_URL is not None:
        return f"{settings.DISCUSSIONS_MICROFRONTEND_URL}/{course_key}/"
    return ''


def get_discussions_mfe_topic_url(course_key: CourseKey, topic_id: str) -> str:
    """
    Returns the url for discussions for the specified course and topic in the discussions MFE.

    Args:
        course_key (CourseKey): course key of course for which to get url
        topic_id (str): topic id for which to generate URL

    Returns:
        (str) URL link for MFE. Empty if the base url isn't configured
    """
    if settings.DISCUSSIONS_MICROFRONTEND_URL is not None:
        return f"{get_discussions_mfe_url(course_key)}topics/{topic_id}"
    return ''
