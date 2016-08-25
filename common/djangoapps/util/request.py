""" Utility functions related to HTTP requests """
import re

from django.conf import settings

from opaque_keys import InvalidKeyError
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

# accommodates course api urls, excluding any course api routes that do not fall under v*/courses, such as v1/blocks.
COURSE_REGEX = re.compile(r'^(.*?/courses/)(?!v[0-9]+/[^/]+){}'.format(settings.COURSE_ID_PATTERN))


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
        return configuration_helpers.get_value('site_domain', settings.SITE_NAME)


def course_id_from_url(url):
    """
    Extracts the course_id from the given `url`.
    """
    if not url:
        return None

    match = COURSE_REGEX.match(url)

    if match is None:
        return None

    course_id = match.group('course_id')

    if course_id is None:
        return None

    try:
        return SlashSeparatedCourseKey.from_deprecated_string(course_id)
    except InvalidKeyError:
        return None
