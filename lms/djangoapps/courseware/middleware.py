"""
Middleware for the courseware app
"""


from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin

from lms.djangoapps.courseware.exceptions import Redirect
from openedx.core.lib.request_utils import COURSE_REGEX


class RedirectMiddleware(MiddlewareMixin):
    """
    Catch Redirect exceptions and redirect the user to the expected URL.
    """
    def process_exception(self, _request, exception):
        """
        Catch Redirect exceptions and redirect the user to the expected URL.
        """
        if isinstance(exception, Redirect):
            return redirect(exception.url)


class CacheCourseIdMiddleware(MiddlewareMixin):
    """Middleware that adds course_id to user request session."""

    def process_request(self, request):
        """
        Add a course_id to user request session.
        """
        if request.user.is_authenticated:
            match = COURSE_REGEX.match(request.build_absolute_uri())
            course_id = None
            if match:
                course_id = match.group('course_id')

            if course_id and course_id != request.session.get('course_id'):
                request.session['course_id'] = course_id
