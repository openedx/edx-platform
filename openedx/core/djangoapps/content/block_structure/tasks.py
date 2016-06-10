"""
Asynchronous tasks related to the Course Blocks sub-application.
"""
import logging
from celery.task import task
from django.conf import settings
from opaque_keys.edx.keys import CourseKey

from . import api

log = logging.getLogger('edx.celery.task')


def _ensure_lms_queue():
    """
    Ensure the worker associated with the chosen queue is loaded with lms params, if available.

    This is needed due to the signal that triggers these tasks coming from cms, which does not have settings
    defined that are required for these tasks.
    """
    queues = getattr(settings, 'CELERY_QUEUES', None)
    lms_queue = next((queue for queue in queues if '.lms.' in queue), None)
    return lms_queue


@task(queue=_ensure_lms_queue())
def update_course_in_cache(course_key):
    """
    Updates the course blocks (in the database) for the specified course.
    """
    course_key = CourseKey.from_string(course_key)
    api.update_course_in_cache(course_key)


@task(queue=_ensure_lms_queue())
def clear_course_from_cache(course_key):
    """
    Deletes the given course from the cache.
    """
    course_key = CourseKey.from_string(course_key)
    api.clear_course_from_cache(course_key)
