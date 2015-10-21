"""
Implementation of "Analytics" service
"""

from eventtracking import tracker


class AnalyticsService(object):
    """
    Analytics service
    """

    def emit_event(self, name, context, data):
        """
        Emit an event annotated with the UTC time when this function was called.
        """

        with tracker.get_tracker().context(name, context):
            tracker.emit(name, data)
