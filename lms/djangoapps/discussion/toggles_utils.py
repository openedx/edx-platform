"""
Utils for Discussions feature toggles
"""
from lms.djangoapps.discussion.toggles import ENABLE_DISCUSSIONS_MFE
from openedx.core.djangoapps.django_comment_common.models import CourseDiscussionSettings


def reported_content_email_notification_enabled(course_key):
    """
    Checks for relevant flag and setting and returns boolean for reported
    content email notification for course
    """
    return bool(ENABLE_DISCUSSIONS_MFE.is_enabled(course_key) and
                CourseDiscussionSettings.get(course_key).reported_content_email_notifications)
