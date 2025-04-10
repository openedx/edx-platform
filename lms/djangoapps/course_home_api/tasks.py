"""
Celery tasks used by the `course_home_api` app.
"""
import logging

from celery import shared_task
from django.contrib.auth import get_user_model
from edx_django_utils.monitoring import set_code_owner_attribute
from eventtracking import tracker
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from common.djangoapps.student.models_api import get_course_enrollment
from lms.djangoapps.courseware.courses import get_course_blocks_completion_summary

User = get_user_model()
COURSE_COMPLETION_FOR_USER_EVENT_NAME = "edx.bi.user.course-progress"

log = logging.getLogger(__name__)


@shared_task
@set_code_owner_attribute
def calculate_course_progress_for_user_in_course(course_id: str, user_id: str) -> None:
    """
    Celery task that calculates a learner's progress in a given course. This task uses the same function as the Progress
    tab in the courseware (Learning MFE) to calculate progress.
    """
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        log.warning(f"Invalid course id {course_id}, aborting task.")
        return

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        log.warning(f"Could not retrieve a user with id {user_id}, aborting task.")
        return

    summary = get_course_blocks_completion_summary(course_key, user)

    complete_units = summary["complete_count"]
    incomplete_units = summary["incomplete_count"]
    locked_units = summary["locked_count"]
    num_total_units = complete_units + incomplete_units + locked_units
    complete_percentage = round(complete_units / num_total_units, 2)

    enrollment = get_course_enrollment(user, course_key)

    data = {
        "user_id": user.id,
        "course_id": course_id,
        "enrollment_mode": enrollment.mode,
        "num_total_units": num_total_units,
        "complete_units": complete_units,
        "incomplete_units": incomplete_units,
        "locked_units": locked_units,
        "complete_percentage": complete_percentage,
    }
    tracker.emit(
        COURSE_COMPLETION_FOR_USER_EVENT_NAME,
        data
    )
