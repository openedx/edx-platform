"""
Middleware for user api.
Adds user's tags to tracking event context.
"""

from eventtracking import tracker
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from track.contexts import COURSE_REGEX

from .models import UserCourseTag


class UserTagsEventContextMiddleware(object):
    """Middleware that adds a user's tags to tracking event context."""
    CONTEXT_NAME = 'user_tags_context'

    def process_request(self, request):
        """
        Add a user's tags to the tracking event context.
        """
        match = COURSE_REGEX.match(request.path)
        course_key = None
        if match:
            course_key = match.group('course_id')
            try:
                course_key = CourseKey.from_string(course_key)
            except InvalidKeyError:
                course_key = None

        context = {}

        if course_key:
            try:
                context['course_id'] = course_key.to_deprecated_string()
            except AttributeError:
                context['course_id'] = unicode(course_key)

            if request.user.is_authenticated():
                context['course_user_tags'] = dict(
                    UserCourseTag.objects.filter(
                        user=request.user.pk,
                        course_id=course_key,
                    ).values_list('key', 'value')
                )
            else:
                context['course_user_tags'] = {}

        tracker.get_tracker().enter_context(
            self.CONTEXT_NAME,
            context
        )

    def process_response(self, request, response):  # pylint: disable=unused-argument
        """Exit the context if it exists."""
        try:
            tracker.get_tracker().exit_context(self.CONTEXT_NAME)
        except:  # pylint: disable=bare-except
            pass

        return response
