""" Utility functions related to HTTP requests """
import logging
import re

from django.conf import settings
from microsite_configuration import microsite
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey

log = logging.getLogger(__name__)


def safe_get_host(request):
    """
    Get the host name for this request, as safely as possible.

    If ALLOWED_HOSTS is properly set, this calls request.get_host;
    otherwise, this returns whatever settings.SITE_NAME is set to.

    This ensures we will never accept an untrusted value of get_host()
    """
    if isinstance(settings.ALLOWED_HOSTS, (list, tuple)) and '*' not in settings.ALLOWED_HOSTS:
        return request.get_host()
    else:
        return microsite.get_value('site_domain', settings.SITE_NAME)


def course_id_from_url(url):
    """
    Extracts the course_id from the given `url`.
    """
    if not url:
        return None

    COURSE_REGEX = re.compile(r'^.*?/courses/(?P<course_id>[a-zA-Z0-9_+\/:]+)')
    match = COURSE_REGEX.match(url)
    if match is None:
        return None
    course_id = match.group('course_id')
    if course_id is None:
        return None

    course_key = None
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        COURSE_REGEX = re.compile(r'(?P<course_id>[^/]+/[^/]+/[^/]+)')
        match = COURSE_REGEX.match(course_id)
        if match is None:
            return None
        course_id = match.group('course_id')
        if course_id is None:
            return None
        try:
            course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        except InvalidKeyError:
            log.warning(
                'unable to parse course_id "{}"'.format(course_id),
                exc_info=True
            )

    return course_key
