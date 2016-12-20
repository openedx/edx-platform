"""
Asynchronous tasks related to the Course Blocks sub-application.
"""
import logging
from celery.task import task
from opaque_keys.edx.keys import CourseKey

from . import api


log = logging.getLogger('edx.celery.task')


@task()
def update_course_in_cache(course_key):
    """
    Updates the course blocks (in the database) for the specified course.
    """
    course_key = CourseKey.from_string(course_key)
    api.update_course_in_cache(course_key)
