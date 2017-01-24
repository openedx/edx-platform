"""
Asynchronous tasks related to the Course Blocks sub-application.
"""
import logging

from capa.responsetypes import LoncapaProblemError
from celery.task import task
from django.conf import settings
from lxml.etree import XMLSyntaxError

from edxval.api import ValInternalError
from opaque_keys.edx.keys import CourseKey

from xmodule.modulestore.exceptions import ItemNotFoundError
from openedx.core.djangoapps.content.block_structure import api

log = logging.getLogger('edx.celery.task')

# TODO: TNL-5799 is ongoing; narrow these lists down until the general exception is no longer needed
RETRY_TASKS = (ItemNotFoundError, TypeError, ValInternalError)
NO_RETRY_TASKS = (XMLSyntaxError, LoncapaProblemError, UnicodeEncodeError)


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
    except NO_RETRY_TASKS as exc:
        # Known unrecoverable errors
        raise
    except RETRY_TASKS as exc:
        log.exception("update_course_in_cache encounted expected error, retrying.")
        raise update_course_in_cache.retry(args=[course_id], exc=exc)
    except Exception as exc:   # pylint: disable=broad-except
        log.exception("update_course_in_cache encounted unknown error. Retry #{}".format(
            update_course_in_cache.request.retries,
        ))
        raise update_course_in_cache.retry(args=[course_id], exc=exc)
