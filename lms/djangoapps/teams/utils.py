"""
Utility methods related to teams.
"""

from django.conf import settings
from eventtracking import tracker
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

from track import contexts


def emit_team_event(event_name, course_key, event_data):
    """
    Emit team events with the correct course id context.
    """
    context = contexts.course_context_from_course_id(course_key)

    with tracker.get_tracker().context(event_name, context):
        tracker.emit(event_name, event_data)


def are_team_submissions_enabled(course_key):
    """
    Checks to see if the CourseWaffleFlag or Django setting for team submissions is enabled

    Returns:
        Boolean value representing switch status
    """
    waffle_namespace = 'openresponseassessment'
    switch_name = 'team_submissions'

    if CourseWaffleFlag(waffle_namespace, switch_name).is_enabled(course_key):
        return True

    feature_name = 'ENABLE_ORA_TEAM_SUBMISSIONS'
    if settings.FEATURES.get(feature_name, False):
        return True

    return False
