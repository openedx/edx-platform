"""
Celery tasks for Content Libraries.
"""


import logging

from celery import shared_task
from celery_utils.logged_task import LoggedTask

from opaque_keys.edx.keys import CourseKey

from . import api


logger = logging.getLogger(__name__)


@shared_task(base=LoggedTask)
def import_blocks_from_course(import_task_id, course_key_str):
    """
    A Celery task to import blocks from a course through modulestore.
    """
    course_key = CourseKey.from_string(course_key_str)
    api.import_blocks_from_course(import_task_id, course_key)
