"""
Middleware for the courseware app
"""

from django.shortcuts import redirect
from django.core.urlresolvers import reverse

from .courses import UserNotEnrolled


class RedirectUnenrolledMiddleware(object):
    """
    Catch UserNotEnrolled errors thrown by `get_course_with_access` and redirect
    users to the course about page
    """
    def process_exception(self, _request, exception):
        if isinstance(exception, UserNotEnrolled):
            course_key = exception.course_key
            return redirect(
                reverse(
                    'lms.djangoapps.courseware.views.views.course_about',
                    args=[course_key.to_deprecated_string()]
                )
            )
