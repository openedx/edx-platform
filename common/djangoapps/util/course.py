"""
Utility methods related to course
"""
import logging

from django.conf import settings
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.catalog.utils import get_run_marketing_url

log = logging.getLogger(__name__)


def get_link_for_about_page(course_key, user):
    """
    Returns the url to the course about page.
    """
    assert isinstance(course_key, CourseKey)

    if settings.FEATURES.get('ENABLE_MKTG_SITE'):
        marketing_url = get_run_marketing_url(course_key, user)
        if marketing_url:
            return marketing_url

    return get_lms_course_about_page_url(course_key)


def get_link_for_about_page_from_cache(course_key, catalog_course_run=None):
    """
    Returns the url to the course about page from already cached dict if marketing
    site is enabled else returns lms course about url.
    """
    if settings.FEATURES.get('ENABLE_MKTG_SITE') and catalog_course_run:
        marketing_url = catalog_course_run.get('marketing_url')
        if marketing_url:
            return marketing_url

    return get_lms_course_about_page_url(course_key)


def get_lms_course_about_page_url(course_key):
    """
    Returns lms about page url for course.
    """
    return u"{about_base_url}/courses/{course_key}/about".format(
        about_base_url=settings.LMS_ROOT_URL,
        course_key=unicode(course_key)
    )
