"""
Asynchronous tasks related to the Course Blocks sub-application.
"""
import logging
from celery.task import task
from django.conf import settings
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.content.block_structure import api

log = logging.getLogger('edx.celery.task')


@task(
    default_retry_delay=settings.BLOCK_STRUCTURES_SETTINGS['BLOCK_STRUCTURES_TASK_DEFAULT_RETRY_DELAY'],
    max_retries=settings.BLOCK_STRUCTURES_SETTINGS['BLOCK_STRUCTURES_TASK_MAX_RETRIES'],
)
def update_course_in_cache(course_id):
    """
    Updates the course blocks (in the database) for the specified course.
    """
    try:
        course_key = CourseKey.from_string(course_id)
        api.update_course_in_cache(course_key)
    except Exception as exc:   # pylint: disable=broad-except
        # TODO: TNL-5799, check splunk logs to narrow down the broad except above
        log.info("update_course_in_cache. Retry #{} for this task, exception: {}".format(
            update_course_in_cache.request.retries,
            repr(exc)
        ))
        raise update_course_in_cache.retry(args=[course_id], exc=exc)
