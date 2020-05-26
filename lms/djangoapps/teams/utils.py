"""
Utility methods related to teams.
"""

from django.conf import settings
from eventtracking import tracker

from track import contexts


def emit_team_event(event_name, course_key, event_data):
    """
    Emit team events with the correct course id context.
    """
    context = contexts.course_context_from_course_id(course_key)

    with tracker.get_tracker().context(event_name, context):
        tracker.emit(event_name, event_data)


def are_team_submissions_enabled():
    """
    Checks to see if the Django setting for team submissions is enabled

    Returns:
        Boolean value representing switch status
    """
    return settings.FEATURES.get('ENABLE_ORA_TEAM_SUBMISSIONS', False)
