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
def update_course_in_cache(course_key):
    """
    Updates the course blocks (in the database) for the specified course.
    """
    course_key = CourseKey.from_string(course_key)
    api.update_course_in_cache(course_key)
