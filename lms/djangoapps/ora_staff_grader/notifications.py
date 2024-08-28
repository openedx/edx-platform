"""
This module contains utility functions for sending notifications.
"""
import logging

from opaque_keys.edx.keys import UsageKey
from opaque_keys import InvalidKeyError


from openedx_events.learning.data import UserNotificationData
from openedx_events.learning.signals import USER_NOTIFICATION_REQUESTED
from openedx.core.djangoapps.content.course_overviews.api import (
    get_course_overview_or_none,
)
from lms.djangoapps.ora_staff_grader.errors import (
    XBlockInternalError,
)
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
from django.contrib.auth import get_user_model
from django.conf import settings

log = logging.getLogger(__name__)
User = get_user_model()


def send_staff_grade_assigned_notification(request, usage_id, submission):
    """
        Send a user notification for a course for a new grade being assigned
    """
    try:
        ora_user = User.objects.get(email=submission['email'])
        # Do not send the notification if the request user is the same as the ora submitter
        if request.user.id != ora_user.id:
            # Get ORA block
            ora_usage_key = UsageKey.from_string(usage_id)
            ora_metadata = modulestore().get_item(ora_usage_key)
            # Get course metadata
            course_id = str(ora_usage_key.course_key)
            course_metadata = get_course_overview_or_none(course_id)
            notification_data = UserNotificationData(
                user_ids=[ora_user.id],
                context={
                    'ora_name': ora_metadata.display_name,
                    'course_name': course_metadata.display_name,
                    'points_earned': submission['score']['pointsEarned'],
                    'points_possible': submission['score']['pointsPossible'],
                },
                notification_type="ora_staff_grade_assigned",
                content_url=f"{settings.LMS_ROOT_URL}/courses/{str(course_id)}/jump_to/{str(ora_usage_key)}",
                app_name="grading",
                course_key=course_id,
            )
            USER_NOTIFICATION_REQUESTED.send_event(notification_data=notification_data)

    # Catch bad ORA location
    except (InvalidKeyError, ItemNotFoundError):
        log.error(f"Bad ORA location provided: {usage_id}")

    # Issues with the XBlock handlers
    except XBlockInternalError as ex:
        log.error(ex)
