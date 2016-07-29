"""
Celery task for Automatic Verifed Track Cohorting MVP feature.
"""
from django.contrib.auth.models import User

from celery.task import task
from celery.utils.log import get_task_logger

from opaque_keys.edx.keys import CourseKey
from student.models import CourseEnrollment, CourseMode
from openedx.core.djangoapps.course_groups.cohorts import (
    get_cohort_by_name, get_cohort, add_user_to_cohort
)

LOGGER = get_task_logger(__name__)


@task(bind=True, default_retry_delay=60, max_retries=4)
def sync_cohort_with_mode(self, course_id, user_id, verified_cohort_name, default_cohort_name):
    """
    If the learner's mode does not match their assigned cohort, move the learner into the correct cohort.
    It is assumed that this task is only initiated for courses that are using the
    Automatic Verified Track Cohorting MVP feature. It is also assumed that before
    initiating this task, verification has been done to ensure that the course is
    cohorted and has an appropriately named "verified" cohort.
    """
    course_key = CourseKey.from_string(course_id)
    user = User.objects.get(id=user_id)
    try:
        enrollment = CourseEnrollment.get_enrollment(user, course_key)
        # Note that this will enroll the user in the default cohort on initial enrollment.
        # That's good because it will force creation of the default cohort if necessary.
        current_cohort = get_cohort(user, course_key)
        verified_cohort = get_cohort_by_name(course_key, verified_cohort_name)

        if enrollment.mode == CourseMode.VERIFIED and (current_cohort.id != verified_cohort.id):
            LOGGER.info(
                "MOVING_TO_VERIFIED: Moving user '%s' to the verified cohort '%s' for course '%s'",
                user.username, verified_cohort.name, course_id
            )
            add_user_to_cohort(verified_cohort, user.username)
        elif enrollment.mode != CourseMode.VERIFIED and current_cohort.id == verified_cohort.id:
            default_cohort = get_cohort_by_name(course_key, default_cohort_name)
            LOGGER.info(
                "MOVING_TO_DEFAULT: Moving user '%s' to the default cohort '%s' for course '%s'",
                user.username, default_cohort.name, course_id
            )
            add_user_to_cohort(default_cohort, user.username)
        else:
            LOGGER.info(
                "NO_ACTION_NECESSARY: No action necessary for user '%s' in course '%s' and enrollment mode '%s'. "
                "The user is already in cohort '%s'.",
                user.username, course_id, enrollment.mode, current_cohort.name
            )
    except Exception as exc:
        LOGGER.warning(
            "SYNC_COHORT_WITH_MODE_RETRY: Exception encountered for course '%s' and user '%s': %s",
            course_id, user.username, unicode(exc)
        )
        raise self.retry(exc=exc)
