"""
Utility methods related to teams.
"""


from eventtracking import tracker

from common.djangoapps.track import contexts


def emit_team_event(event_name, course_key, event_data):
    """
    Emit team events with the correct course id context.
    """
    context = contexts.course_context_from_course_id(course_key)

    with tracker.get_tracker().context(event_name, context):
        tracker.emit(event_name, event_data)
