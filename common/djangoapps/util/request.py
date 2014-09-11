""" Utility functions related to HTTP requests """
import logging
import re

from django.conf import settings
from django.core.handlers.base import BaseHandler
from django.test.client import RequestFactory

from microsite_configuration import microsite
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locations import SlashSeparatedCourseKey

log = logging.getLogger(__name__)

COURSE_REGEX = re.compile(r'^.*?/courses/{}'.format(settings.COURSE_ID_PATTERN))


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

    try:
        return SlashSeparatedCourseKey.from_deprecated_string(course_id)
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


class RequestMock(RequestFactory):
    """
    RequestMock is used to create generic/dummy request objects in
    scenarios where a regular request might not be available for use
    """
    def request(self, **request):
        "Construct a generic request object."
        request = RequestFactory.request(self, **request)
        handler = BaseHandler()
        handler.load_middleware()
        for middleware_method in handler._request_middleware:
            if middleware_method(request):
                raise Exception("Couldn't create request mock object - "
                                "request middleware returned a response")
        return request


class RequestMockWithoutMiddleware(RequestMock):
    """
    RequestMockWithoutMiddleware is used to create generic/dummy request
    objects in scenarios where a regular request might not be available for use.
    It's similiar to its parent except for the fact that it skips the loading
    of middleware.
    """
    def request(self, **request):
        "Construct a generic request object."
        request = RequestFactory.request(self, **request)
        if not hasattr(request, 'session'):
            request.session = {}
        return request
