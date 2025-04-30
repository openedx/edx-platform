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
from lms.djangoapps.course_home_api.progress.api import calculate_progress_for_learner_in_course

User = get_user_model()
COURSE_COMPLETION_FOR_USER_EVENT_NAME = "edx.bi.user.course-progress"

log = logging.getLogger(__name__)


@shared_task
@set_code_owner_attribute
def collect_progress_for_user_in_course(course_id: str, user_id: str) -> None:
    """
    Celery task that retrieves a learner's progress in a given course.
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

    progress = calculate_progress_for_learner_in_course(course_key, user)
    enrollment = get_course_enrollment(user, course_key)
    # add a few extra fields to the returned data to make the event payload a bit more usable
    progress["user_id"] = user.id
    progress["course_id"] = course_id
    progress["enrollment_mode"] = enrollment.mode

    tracker.emit(
        COURSE_COMPLETION_FOR_USER_EVENT_NAME,
        progress
    )
