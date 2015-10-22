"""
Implementation of "Analytics" service
"""

from eventtracking import tracker

from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError


class AnalyticsService(object):
    """
    Analytics service
    """

    def emit_event(self, name, context, data):
        """
        Emit an event annotated with the UTC time when this function was called.
        """

        if context:
            # try to parse out the org_id from the course_id
            if 'course_id' in context:
                try:
                    course_key = CourseKey.from_string(context['course_id'])
                    context['org_id'] = course_key.org
                except InvalidKeyError:
                    # leave org_id blank
                    pass

            with tracker.get_tracker().context(name, context):
                tracker.emit(name, data)
        else:
            # if None is passed in then we don't construct the 'with' context stack
            tracker.emit(name, data)
