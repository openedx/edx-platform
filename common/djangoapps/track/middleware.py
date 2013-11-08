import json
import re

from django.conf import settings

from track import views
from track import contexts
from eventtracking import tracker


COURSE_CONTEXT_NAME = 'edx.course'


class TrackMiddleware(object):
    def process_request(self, request):
        try:
            self.enter_course_context(request)

            if not self.should_process_request(request):
                return

            # Removes passwords from the tracking logs
            # WARNING: This list needs to be changed whenever we change
            # password handling functionality.
            #
            # As of the time of this comment, only 'password' is used
            # The rest are there for future extension.
            #
            # Passwords should never be sent as GET requests, but
            # this can happen due to older browser bugs. We censor
            # this too.
            #
            # We should manually confirm no passwords make it into log
            # files when we change this.

            censored_strings = ['password', 'newpassword', 'new_password',
                                'oldpassword', 'old_password']
            post_dict = dict(request.POST)
            get_dict = dict(request.GET)
            for string in censored_strings:
                if string in post_dict:
                    post_dict[string] = '*' * 8
                if string in get_dict:
                    get_dict[string] = '*' * 8

            event = {'GET': dict(get_dict),
                      'POST': dict(post_dict)}

            # TODO: Confirm no large file uploads
            event = json.dumps(event)
            event = event[:512]

            views.server_track(request, request.META['PATH_INFO'], event)
        except:
            pass

    def should_process_request(self, request):
        """Don't track requests to the specified URL patterns"""
        path = request.META['PATH_INFO']

        ignored_url_patterns = getattr(settings, 'TRACKING_IGNORE_URL_PATTERNS', [])
        for pattern in ignored_url_patterns:
            # Note we are explicitly relying on python's internal caching of
            # compiled regular expressions here.
            if re.match(pattern, path):
                return False
        return True

    def enter_course_context(self, request):
        """
        Extract course information from the request and add it to the
        tracking context.
        """
        tracker.get_tracker().enter_context(
            COURSE_CONTEXT_NAME,
            contexts.course_context_from_url(request.build_absolute_uri())
        )

    def process_response(self, request, response):  # pylint: disable=unused-argument
        """Exit the course context if it exists."""
        try:
            tracker.get_tracker().exit_context(COURSE_CONTEXT_NAME)
        except:  # pylint: disable=bare-except
            pass

        return response
