"""
This file contains celery tasks for credentials-related functionality.
"""


from celery import task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth.models import User
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.credentials.utils import get_credentials_api_client

logger = get_task_logger(__name__)

# Under cms the following setting is not defined, leading to errors during tests.
# These tasks aren't strictly credentials generation, but are similar in the sense
# that they generate records on the credentials side. And have a similar SLA.
ROUTING_KEY = getattr(settings, 'CREDENTIALS_GENERATION_ROUTING_KEY', None)

# Maximum number of retries before giving up.
# For reference, 11 retries with exponential backoff yields a maximum waiting
# time of 2047 seconds (about 30 minutes). Setting this to None could yield
# unwanted behavior: infinite retries.
MAX_RETRIES = 11


@task(bind=True, ignore_result=True, routing_key=ROUTING_KEY)
def send_grade_to_credentials(self, username, course_run_key, verified, letter_grade, percent_grade):
    """ Celery task to notify the Credentials IDA of a grade change via POST. """
    logger.info(u'Running task send_grade_to_credentials for username %s and course %s', username, course_run_key)

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

        logger.info(u'Sent grade for course %s to user %s', course_run_key, username)

    except Exception as exc:
        logger.exception(u'Failed to send grade for course %s to user %s', course_run_key, username)
        raise self.retry(exc=exc, countdown=countdown, max_retries=MAX_RETRIES)
