"""
Utility methods related to course
"""
import logging
from django.conf import settings

log = logging.getLogger(__name__)


def get_link_for_about_page(course):
    """
    Arguments:
        course: This can be either a course overview object or a course descriptor.

    Returns the course sharing url, this can be one of course's social sharing url, marketing url, or
    lms course about url.
    """
    is_social_sharing_enabled = getattr(settings, 'SOCIAL_SHARING_SETTINGS', {}).get('CUSTOM_COURSE_URLS')
    if is_social_sharing_enabled and course.social_sharing_url:
        course_about_url = course.social_sharing_url
    elif settings.FEATURES.get('ENABLE_MKTG_SITE') and getattr(course, 'marketing_url', None):
        course_about_url = course.marketing_url
    else:
        course_about_url = u'{about_base_url}/courses/{course_key}/about'.format(
            about_base_url=settings.LMS_ROOT_URL,
            course_key=unicode(course.id),
        )

    return course_about_url
