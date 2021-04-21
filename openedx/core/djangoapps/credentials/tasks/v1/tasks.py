"""
This file contains celery tasks for credentials-related functionality.
"""


from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from edx_django_utils.monitoring import set_code_owner_attribute
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.credentials.utils import get_credentials_api_client

logger = get_task_logger(__name__)

# Maximum number of retries before giving up.
# For reference, 11 retries with exponential backoff yields a maximum waiting
# time of 2047 seconds (about 30 minutes). Setting this to None could yield
# unwanted behavior: infinite retries.
MAX_RETRIES = 11


@shared_task(bind=True, ignore_result=True)
@set_code_owner_attribute
def send_grade_to_credentials(self, username, course_run_key, verified, letter_grade, percent_grade):
    """ Celery task to notify the Credentials IDA of a grade change via POST. """
    logger.info(f"Running task send_grade_to_credentials for username {username} and course {course_run_key}")

    countdown = 2 ** self.request.retries
    course_key = CourseKey.from_string(course_run_key)

    try:
        credentials_client = get_credentials_api_client(
            User.objects.get(username=settings.CREDENTIALS_SERVICE_USERNAME),
            org=course_key.org,
        )

        credentials_client.grades.post({
            'username': username,
            'course_run': str(course_key),
            'letter_grade': letter_grade,
            'percent_grade': percent_grade,
            'verified': verified,
        })

        logger.info(f"Sent grade for course {course_run_key} to user {username}")

    except Exception as exc:  # lint-amnesty, pylint: disable=unused-variable
        error_msg = f"Failed to send grade for course {course_run_key} to user {username}."
        logger.exception(error_msg)
        exception = MaxRetriesExceededError(
            f"Failed to send grade to credentials. Reason: {error_msg}"
        )
        raise self.retry(exc=exception, countdown=countdown, max_retries=MAX_RETRIES)
