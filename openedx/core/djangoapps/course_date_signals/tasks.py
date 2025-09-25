"""
Celery task for course date signals.
"""
from typing import NoReturn

from celery import shared_task
from celery.utils.log import get_task_logger
from django.contrib.auth import get_user_model
from edx_django_utils.monitoring import set_code_owner_attribute
from edx_when.api import update_or_create_assignments_due_dates, UserDateHandler

from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.courseware.courses import get_course_assignments


User = get_user_model()


LOGGER = get_task_logger(__name__)
USER_BATCH_SIZE = 500


@shared_task
@set_code_owner_attribute
def update_assignment_dates_for_course(course_key_str):
    """
    Celery task to update assignment dates for a course.
    """
    try:
        LOGGER.info("Starting to update assignment dates for course %s", course_key_str)
        course_key = CourseKey.from_string(course_key_str)
        staff_user = User.objects.filter(is_staff=True).first()
        if not staff_user:
            LOGGER.error("No staff user found to update assignment dates for course %s", course_key_str)
            return
        assignments = get_course_assignments(course_key, staff_user)
        update_or_create_assignments_due_dates(course_key, assignments)
        LOGGER.info("Successfully updated assignment dates for course %s", course_key_str)
    except Exception:  # pylint: disable=broad-except
        LOGGER.exception("Could not update assignment dates for course %s", course_key_str)
        raise


@shared_task
@set_code_owner_attribute
def user_dates_on_enroll_task(user_id: int, course_key: str) -> None | NoReturn:
    """
    Generate UserDate records when a user enrolls in a course.

    Args:
        user_id (int): ID of the enrolled user
        course_key (str): key identifying the course
    """
    LOGGER.debug(f"Starting to create user dates on enrollment for user_id={user_id} in {course_key}")
    try:
        course_key_obj = CourseKey.from_string(course_key)
        assignments = get_course_assignments(
            course_key_obj,
            User.objects.get(pk=user_id),
            include_access=True
        )
        course_overview = CourseOverview.get_from_id(course_key_obj)
        course_data = {
            "start": course_overview.start,
            "end": course_overview.end,
            "location": str(course_overview.location),
        }
        UserDateHandler(course_key).create_for_user(user_id, assignments, course_data)
        LOGGER.debug(f"Successfully created user dates on enrollment for user_id={user_id} in {course_key}")
    except Exception:  # pylint: disable=broad-except
        LOGGER.exception(f"Could not create user dates on enrollment for user_id={user_id} in {course_key}")
        raise


@shared_task
@set_code_owner_attribute
def user_dates_on_unenroll_task(user_id, course_key) -> None | NoReturn:
    """
    Remove UserDate records when a user unenrolls from a course.

    Args:
        user_id (int): ID of the unenrolled user
        course_key (str): key identifying the course
    """
    LOGGER.debug(f"Starting to delete user dates on unenrollment for user_id={user_id} in {course_key}")
    try:
        deleted = UserDateHandler(course_key).delete_for_user(user_id)
        LOGGER.debug(
            f"Successfully deleted user dates on unenrollment for user_id={user_id} in {course_key}: {deleted}"
        )
    except Exception:  # pylint: disable=broad-except
        LOGGER.exception(f"Could not delete user dates on unenrollment for user_id={user_id} in {course_key}")
        raise


@shared_task
@set_code_owner_attribute
def user_dates_on_cohort_change_task(user_id: int, course_key: str) -> None | NoReturn:
    """
    Synchronize UserDate records when a user's cohort membership changes (added to, or removed from, a cohort).

    Args:
        user_id (int): ID of the user whose cohort membership changed
        course_key (str): key identifying the course
    """
    LOGGER.debug(f"Starting to sync user dates on cohort membership change for user_id={user_id} in {course_key}")
    try:
        assignments = get_course_assignments(
            CourseKey.from_string(course_key),
            User.objects.get(pk=user_id),
            include_access=True
        )
        UserDateHandler(course_key).sync_for_user(user_id, assignments)
        LOGGER.debug(
            f"Successfully synced user dates on cohort membership change for user_id={user_id} in {course_key}"
        )
    except Exception:  # pylint: disable=broad-except
        LOGGER.exception(
            f"Could not update user dates on cohort membership change for user_id={user_id} in {course_key}"
        )
        raise


@shared_task
@set_code_owner_attribute
def user_dates_on_course_publish_task(course_key: str) -> None | NoReturn:
    """
    Trigger batch synchronization of UserDate records for all users in the course when any course content is published.

    Args:
        course_key (str): key identifying the course
    """
    LOGGER.debug(f"Starting to sync user dates on publishing {course_key}")
    try:
        course_key_obj = CourseKey.from_string(course_key)
        course_overview = CourseOverview.get_from_id(course_key_obj)
        course_data = {
            "start": course_overview.start,
            "end": course_overview.end,
            "location": str(course_overview.location),
        }
        user_ids = list(
            CourseEnrollment.objects.filter(course_id=course_key, is_active=True).values_list("user_id", flat=True)
        )
        for i in range(0, len(user_ids), USER_BATCH_SIZE):
            batch = user_ids[i:i + USER_BATCH_SIZE]
            sync_user_dates_batch_task.delay(batch, course_key, course_data)
        LOGGER.debug(f"Successfully completed syncing user dates on publishing {course_key}")
    except Exception:  # pylint: disable=broad-except
        LOGGER.exception(f"Could not sync user dates on publishing {course_key}")
        raise


@shared_task
@set_code_owner_attribute
def sync_user_dates_batch_task(user_ids: list, course_key: str, course_data: dict) -> None | NoReturn:
    """
    Synchronize UserDate records for a batch of users.
    """
    LOGGER.debug(f"Starting to sync user dates for a batch of {len(user_ids)} users in {course_key}")
    try:
        course_key_obj = CourseKey.from_string(course_key)
        user_date_handler = UserDateHandler(course_key)

        for user_id in user_ids:
            assignments = get_course_assignments(course_key_obj, User.objects.get(id=user_id), include_access=True)
            user_date_handler.sync_for_user(user_id, assignments, course_data)
        LOGGER.debug(f"Successfully completed syncing user dates for a batch of {len(user_ids)} users in {course_key}")
    except Exception:  # pylint: disable=broad-except
        LOGGER.exception(f"Could not batch sync user dates for {course_key}")
        raise
