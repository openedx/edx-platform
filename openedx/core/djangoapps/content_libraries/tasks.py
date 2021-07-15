"""
Celery tasks for Content Libraries.
"""


import logging

from celery import shared_task
from celery_utils.logged_task import LoggedTask

from opaque_keys.edx.keys import CourseKey

from . import api
from .models import ContentLibraryBlockImportTask


logger = logging.getLogger(__name__)


@shared_task(base=LoggedTask)
def import_blocks_from_course(import_task_id, course_key_str):
    """
    A Celery task to import blocks from a course through modulestore.
    """

    course_key = CourseKey.from_string(course_key_str)

    with ContentLibraryBlockImportTask.execute(import_task_id) as import_task:

        def on_progress(block_key, block_num, block_count, exception=None):
            if exception:
                logger.exception('Import block failed: %s', block_key)
            else:
                logger.info('Import block succesful: %s', block_key)
            import_task.save_progress(block_num / block_count)

        edx_client = api.EdxModulestoreImportClient(library=import_task.library)
        edx_client.import_blocks_from_course(
            course_key, on_progress
        )
