"""
Celery task for Automatic Verifed Track Cohorting MVP feature.
"""


import six

from celery.task import task
from celery.utils.log import get_task_logger
from django.contrib.auth.models import User
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.course_groups.cohorts import add_user_to_cohort, get_cohort, get_cohort_by_name
from common.djangoapps.student.models import CourseEnrollment, CourseMode

LOGGER = get_task_logger(__name__)


@task(bind=True, default_retry_delay=60, max_retries=2)
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

        acceptable_modes = {CourseMode.VERIFIED, CourseMode.CREDIT_MODE}
        if enrollment.mode in acceptable_modes and (current_cohort.id != verified_cohort.id):
            LOGGER.info(
                u"MOVING_TO_VERIFIED: Moving user '%s' to the verified cohort '%s' for course '%s'",
                user.id, verified_cohort.name, course_id
            )
            add_user_to_cohort(verified_cohort, user.username)
        elif enrollment.mode not in acceptable_modes and current_cohort.id == verified_cohort.id:
            default_cohort = get_cohort_by_name(course_key, default_cohort_name)
            LOGGER.info(
                u"MOVING_TO_DEFAULT: Moving user '%s' to the default cohort '%s' for course '%s'",
                user.id, default_cohort.name, course_id
            )
            add_user_to_cohort(default_cohort, user.username)
        else:
            LOGGER.info(
                u"NO_ACTION_NECESSARY: No action necessary for user '%s' in course '%s' and enrollment mode '%s'. "
                u"The user is already in cohort '%s'.",
                user.id, course_id, enrollment.mode, current_cohort.name
            )
    except Exception as exc:
        LOGGER.warning(
            u"SYNC_COHORT_WITH_MODE_RETRY: Exception encountered for course '%s' and user '%s': %s",
            course_id, user.id, six.text_type(exc)
        )
        raise self.retry(exc=exc)
