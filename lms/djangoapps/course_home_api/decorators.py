"""
Decorators for Course Home APIs.
"""

import functools

from django.http import QueryDict
from django.urls import reverse
from rest_framework.response import Response

from lms.djangoapps.courseware.courseware_access_exception import CoursewareAccessException
from lms.djangoapps.courseware.exceptions import Redirect


def course_home_redirects(func):
    """
    Method decorator for a course home API endpoint that verifies the user has access to the course.

    A lot of old platform code is written in a way that assumes the request is for the main html page, rather than an
    ajax call. So it will frequently raise redirect exceptions in cases like access errors.

    However for ajax calls, the browser will follow those redirects and try to parse some html page as json. So we need
    to instead return some json that tells the frontend to change browser locations.

    And that's what this decorator does. It handles the following exceptions, thrown by your wrapped method:

    * courseware.courseware_access_exception.CoursewareAccessException:
      - generic access error
      - we'll redirect to the dashboard with your error message

    * courseware.exceptions.Redirect (and its subclasses like courseware.exceptions.CourseAccessRedirect):
      - used for a most access errors
      - we'll redirect to the provided url, making it absolute first

    The response we give, which the frontend knows how to parse, looks like a standard 403 response, with a json body:
    {
        'redirect': 'https://.../my/new/path'
    }

    We use 403 as the error code just because it roughly matches the usual reason for these redirects (permission
    denied) but also because at the time of writing, the MFE does not already have conflicting handling for 403.
    Really, the error code can be anything, as long as the MFE knows to parse it for the redirect. The browser/user
    does not need to understand the error code as having any particular meaning. So 403 it is.

    (Remember that we can't simply return a 3xx status code because the browser will automatically follow those, and
     you can't ask it not to. So the MFE would end up trying to parse html as json.)
    """
    @functools.wraps(func)
    def _wrapper(self, request, *args, **kwargs):
        """This is the actual function wrapper that handles exceptions"""

        def create_response(url):
            return Response(status=403, data={'redirect': request.build_absolute_uri(url)})

        try:
            return func(self, request, *args, **kwargs)
        except CoursewareAccessException as exc:
            # Extend this 404 exception with a redirect to the user's dashboard, plus an error message.
            params = QueryDict(mutable=True)
            # Prefer a message with course context, if available
            user_message = exc.access_response.additional_context_user_message or exc.access_response.user_message
            if user_message:
                params['access_response_error'] = user_message
            return create_response('{dashboard_url}?{params}'.format(
                dashboard_url=reverse('dashboard'),
                params=params.urlencode(),
            ))
        except Redirect as exc:
            return create_response(exc.url)

    return _wrapper
