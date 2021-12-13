""" receivers of course_published and library_updated events in order to trigger indexing task """


import logging
from datetime import datetime
from functools import wraps

from django.core.cache import cache
from django.dispatch import receiver
from pytz import UTC

from cms.djangoapps.contentstore.courseware_index import (
    CourseAboutSearchIndexer,
    CoursewareSearchIndexer,
    LibrarySearchIndexer,
)
from common.djangoapps.track.event_transaction_utils import get_event_transaction_id, get_event_transaction_type
from common.djangoapps.util.module_utils import yield_dynamic_descriptor_descendants
from lms.djangoapps.grades.api import task_compute_all_grades_for_course
from openedx.core.djangoapps.content.learning_sequences.api import key_supports_outlines
from openedx.core.djangoapps.discussions.tasks import update_discussions_settings_from_course_task
from openedx.core.lib.gating import api as gating_api
from xmodule.modulestore.django import SignalHandler, modulestore  # lint-amnesty, pylint: disable=wrong-import-order
from .signals import GRADING_POLICY_CHANGED

log = logging.getLogger(__name__)

GRADING_POLICY_COUNTDOWN_SECONDS = 3600


def locked(expiry_seconds, key):  # lint-amnesty, pylint: disable=missing-function-docstring
    def task_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f'{func.__name__}-{kwargs[key]}'
            if cache.add(cache_key, "true", expiry_seconds):
                log.info('Locking task in cache with key: %s for %s seconds', cache_key, expiry_seconds)
                return func(*args, **kwargs)
            else:
                log.info('Task with key %s already exists in cache', cache_key)
        return wrapper
    return task_decorator


@receiver(SignalHandler.course_published)
def listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Receives publishing signal and performs publishing related workflows, such as
    registering proctored exams, building up credit requirements, and performing
    search indexing
    """
    # import here, because signal is registered at startup, but items in tasks are not yet able to be loaded
    from cms.djangoapps.contentstore.tasks import (
        update_outline_from_modulestore_task,
        update_search_index,
        update_special_exams_and_publish
    )

    # register special exams asynchronously
    course_key_str = str(course_key)
    update_special_exams_and_publish.delay(course_key_str)

    if key_supports_outlines(course_key):
        # Push the course outline to learning_sequences asynchronously.
        update_outline_from_modulestore_task.delay(course_key_str)

    # Finally, call into the course search subsystem
    # to kick off an indexing action
    if CoursewareSearchIndexer.indexing_is_enabled() and CourseAboutSearchIndexer.indexing_is_enabled():
        update_search_index.delay(course_key_str, datetime.now(UTC).isoformat())

    update_discussions_settings_from_course_task.delay(course_key_str)


@receiver(SignalHandler.course_deleted)
def listen_for_course_delete(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been deleted
    and removes its entry from the Course About Search index.
    """
    CourseAboutSearchIndexer.remove_deleted_items(course_key)


@receiver(SignalHandler.library_updated)
def listen_for_library_update(sender, library_key, **kwargs):  # pylint: disable=unused-argument
    """
    Receives signal and kicks off celery task to update search index
    """

    if LibrarySearchIndexer.indexing_is_enabled():
        # import here, because signal is registered at startup, but items in tasks are not yet able to be loaded
        from cms.djangoapps.contentstore.tasks import update_library_index

        update_library_index.delay(str(library_key), datetime.now(UTC).isoformat())


@receiver(SignalHandler.item_deleted)
def handle_item_deleted(**kwargs):
    """
    Receives the item_deleted signal sent by Studio when an XBlock is removed from
    the course structure and removes any gating milestone data associated with it or
    its descendants.

    Arguments:
        kwargs (dict): Contains the content usage key of the item deleted

    Returns:
        None
    """

    usage_key = kwargs.get('usage_key')
    if usage_key:
        # Strip branch info
        usage_key = usage_key.for_branch(None)
        course_key = usage_key.course_key
        deleted_module = modulestore().get_item(usage_key)
        for module in yield_dynamic_descriptor_descendants(deleted_module, kwargs.get('user_id')):
            # Remove prerequisite milestone data
            gating_api.remove_prerequisite(module.location)
            # Remove any 'requires' course content milestone relationships
            gating_api.set_required_content(course_key, module.location, None, None, None)


@receiver(GRADING_POLICY_CHANGED)
@locked(expiry_seconds=GRADING_POLICY_COUNTDOWN_SECONDS, key='course_key')
def handle_grading_policy_changed(sender, **kwargs):
    # pylint: disable=unused-argument
    """
    Receives signal and kicks off celery task to recalculate grades
    """
    kwargs = {
        'course_key': str(kwargs.get('course_key')),
        'grading_policy_hash': str(kwargs.get('grading_policy_hash')),
        'event_transaction_id': str(get_event_transaction_id()),
        'event_transaction_type': str(get_event_transaction_type()),
    }
    result = task_compute_all_grades_for_course.apply_async(kwargs=kwargs, countdown=GRADING_POLICY_COUNTDOWN_SECONDS)
    log.info("Grades: Created {task_name}[{task_id}] with arguments {kwargs}".format(
        task_name=task_compute_all_grades_for_course.name,
        task_id=result.task_id,
        kwargs=kwargs,
    ))
