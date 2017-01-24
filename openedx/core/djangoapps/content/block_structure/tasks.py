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
    bind=True,
)
def update_course_in_cache(self, course_id):
    """
    Updates the course blocks (in the database) for the specified course.
    """
    _call_and_retry_if_needed(course_id, api.update_course_in_cache, update_course_in_cache, self.request.id)


@task(
    default_retry_delay=settings.BLOCK_STRUCTURES_SETTINGS['BLOCK_STRUCTURES_TASK_DEFAULT_RETRY_DELAY'],
    max_retries=settings.BLOCK_STRUCTURES_SETTINGS['BLOCK_STRUCTURES_TASK_MAX_RETRIES'],
    bind=True,
)
def get_course_in_cache(self, course_id):
    """
    Gets the course blocks for the specified course, updating the cache if needed.
    """
    _call_and_retry_if_needed(course_id, api.get_course_in_cache, get_course_in_cache, self.request.id)


def _call_and_retry_if_needed(course_id, api_method, task_method, task_id):
    """
    Calls the given api_method with the given course_id, retrying task_method upon failure.
    """
    try:
        course_key = CourseKey.from_string(course_id)
        api_method(course_key)
    except NO_RETRY_TASKS as exc:
        # Known unrecoverable errors
        log.exception(
            "update_course_in_cache encountered unrecoverable error in course {}, task_id {}".format(
                course_id,
                task_id
            )
        )
        raise
    except RETRY_TASKS as exc:
        log.exception("%s encountered expected error, retrying.", task_method.__name__)
        raise task_method.retry(args=[course_id], exc=exc)
    except Exception as exc:   # pylint: disable=broad-except
        log.exception(
            "%s encountered unknown error. Retry #%d",
            task_method.__name__,
            task_method.request.retries,
        )
        raise task_method.retry(args=[course_id], exc=exc)
