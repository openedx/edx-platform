"""
Utility functions for transcripts dealing with Django models.
"""
from openedx.core.djangoapps.video_config.models import VideoTranscriptEnabledFlag


def is_val_transcript_feature_enabled_for_course(course_id):
    """
    Get edx-val transcript feature flag

    Arguments:
        course_id(CourseKey): Course key identifying a course whose feature flag is being inspected.
    """
    return VideoTranscriptEnabledFlag.feature_enabled(course_id=course_id)
