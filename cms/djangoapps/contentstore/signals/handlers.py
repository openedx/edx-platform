""" receivers of course_published and library_updated events in order to trigger indexing task """


import logging
from datetime import datetime
from functools import wraps

import six
from django.core.cache import cache
from django.dispatch import receiver
from pytz import UTC

from cms.djangoapps.contentstore.courseware_index import CoursewareSearchIndexer, CourseAboutSearchIndexer, LibrarySearchIndexer
from cms.djangoapps.contentstore.proctoring import register_special_exams
from lms.djangoapps.grades.api import task_compute_all_grades_for_course
from openedx.core.djangoapps.credit.signals import on_course_publish
from openedx.core.lib.gating import api as gating_api
from common.djangoapps.track.event_transaction_utils import get_event_transaction_id, get_event_transaction_type
from common.djangoapps.util.module_utils import yield_dynamic_descriptor_descendants
from xmodule.modulestore.django import SignalHandler, modulestore

from .signals import GRADING_POLICY_CHANGED

log = logging.getLogger(__name__)

GRADING_POLICY_COUNTDOWN_SECONDS = 3600


def locked(expiry_seconds, key):
    def task_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = '{}-{}'.format(func.__name__, kwargs[key])
            if cache.add(cache_key, "true", expiry_seconds):
                log.info(u'Locking task in cache with key: %s for %s seconds', cache_key, expiry_seconds)
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

    # first is to registered exams, the credit subsystem will assume that
    # all proctored exams have already been registered, so we have to do that first
    try:
        register_special_exams(course_key)
    # pylint: disable=broad-except
    except Exception as exception:
        log.exception(exception)

    # then call into the credit subsystem (in /openedx/djangoapps/credit)
    # to perform any 'on_publish' workflow
    on_course_publish(course_key)

    # Finally call into the course search subsystem
    # to kick off an indexing action
    if CoursewareSearchIndexer.indexing_is_enabled() and CourseAboutSearchIndexer.indexing_is_enabled():
        # import here, because signal is registered at startup, but items in tasks are not yet able to be loaded
        from cms.djangoapps.contentstore.tasks import update_search_index

        update_search_index.delay(six.text_type(course_key), datetime.now(UTC).isoformat())


@receiver(SignalHandler.library_updated)
def listen_for_library_update(sender, library_key, **kwargs):  # pylint: disable=unused-argument
    """
    Receives signal and kicks off celery task to update search index
    """

    if LibrarySearchIndexer.indexing_is_enabled():
        # import here, because signal is registered at startup, but items in tasks are not yet able to be loaded
        from cms.djangoapps.contentstore.tasks import update_library_index

        update_library_index.delay(six.text_type(library_key), datetime.now(UTC).isoformat())


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
        'course_key': six.text_type(kwargs.get('course_key')),
        'grading_policy_hash': six.text_type(kwargs.get('grading_policy_hash')),
        'event_transaction_id': six.text_type(get_event_transaction_id()),
        'event_transaction_type': six.text_type(get_event_transaction_type()),
    }
    result = task_compute_all_grades_for_course.apply_async(kwargs=kwargs, countdown=GRADING_POLICY_COUNTDOWN_SECONDS)
    log.info(u"Grades: Created {task_name}[{task_id}] with arguments {kwargs}".format(
        task_name=task_compute_all_grades_for_course.name,
        task_id=result.task_id,
        kwargs=kwargs,
    ))
