"""
Middleware for the courseware app
"""

from django.shortcuts import redirect

from lms.djangoapps.courseware.exceptions import Redirect


class RedirectMiddleware(object):
    """
    Catch Redirect exceptions and redirect the user to the expected URL.
    """
    def process_exception(self, _request, exception):
        """
        Catch Redirect exceptions and redirect the user to the expected URL.
        """
        if isinstance(exception, Redirect):
            return redirect(exception.url)
