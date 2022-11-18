""" receivers of course_published and library_updated events in order to trigger indexing task """


import logging
from datetime import datetime
from functools import wraps
from typing import Optional

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.dispatch import receiver
from edx_toggles.toggles import SettingToggle
from edx_event_bus_kafka import get_producer
from opaque_keys.edx.keys import CourseKey
from openedx_events.content_authoring.data import CourseCatalogData, CourseScheduleData
from openedx_events.content_authoring.signals import COURSE_CATALOG_INFO_CHANGED
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
from openedx.core.djangoapps.models.course_details import CourseDetails
from openedx.core.lib.gating import api as gating_api
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import SignalHandler, modulestore
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


# .. toggle_name: SEND_CATALOG_INFO_SIGNAL
# .. toggle_implementation: SettingToggle
# .. toggle_default: False
# .. toggle_description: When True, sends to catalog-info-changed signal when course_published occurs.
#   This is a temporary toggle to allow us to test the event bus integration; it should be removed and
#   always-on once the integration is well-tested and the error cases are handled. (This is separate
#   from whether the event bus itself is configured; if this toggle is on but the event bus is not
#   configured, we should expect a warning at most.)
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2022-08-22
# .. toggle_target_removal_date: 2022-10-30
# .. toggle_tickets: https://github.com/openedx/edx-platform/issues/30682
SEND_CATALOG_INFO_SIGNAL = SettingToggle('SEND_CATALOG_INFO_SIGNAL', default=False, module_name=__name__)


def create_catalog_data_for_signal(course_key: CourseKey) -> Optional[CourseCatalogData]:
    """
    Creates data for catalog-info-changed signal when course is published.

    Arguments:
        course_key: Key of the course to announce catalog info changes for

    Returns:
        Data for signal, or None if not appropriate to send on this signal.
    """
    # Only operate on real courses, not libraries.
    if not course_key.is_course:
        return None

    store = modulestore()
    with store.branch_setting(ModuleStoreEnum.Branch.published_only, course_key):
        course = store.get_course(course_key)

        return CourseCatalogData(
            course_key=course_key.for_branch(None),  # Shouldn't be necessary, but just in case...
            name=course.display_name,
            schedule_data=CourseScheduleData(
                start=course.start,
                pacing='self' if course.self_paced else 'instructor',
                end=course.end,
                enrollment_start=course.enrollment_start,
                enrollment_end=course.enrollment_end,
            ),
            effort=CourseDetails.fetch_about_attribute(course_key, 'effort'),
            hidden=course.catalog_visibility in ['about', 'none'] or course_key.deprecated,
            invitation_only=course.invitation_only,
        )


def emit_catalog_info_changed_signal(course_key: CourseKey):
    """
    Given the key of a recently published course, send course data to catalog-info-changed signal.
    """
    if SEND_CATALOG_INFO_SIGNAL.is_enabled():
        catalog_info = create_catalog_data_for_signal(course_key)
        if catalog_info is not None:
            COURSE_CATALOG_INFO_CHANGED.send_event(catalog_info=catalog_info)


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
    from cms.djangoapps.coursegraph.tasks import (
        dump_course_to_neo4j
    )

    # register special exams asynchronously
    course_key_str = str(course_key)
    update_special_exams_and_publish.delay(course_key_str)

    if key_supports_outlines(course_key):
        # Push the course outline to learning_sequences asynchronously.
        update_outline_from_modulestore_task.delay(course_key_str)

    if settings.COURSEGRAPH_DUMP_COURSE_ON_PUBLISH:
        # Push the course out to CourseGraph asynchronously.
        dump_course_to_neo4j.delay(course_key_str)

    # Finally, call into the course search subsystem
    # to kick off an indexing action
    if CoursewareSearchIndexer.indexing_is_enabled() and CourseAboutSearchIndexer.indexing_is_enabled():
        update_search_index.delay(course_key_str, datetime.now(UTC).isoformat())

    update_discussions_settings_from_course_task.apply_async(
        args=[course_key_str],
        countdown=settings.DISCUSSION_SETTINGS['COURSE_PUBLISH_TASK_DELAY'],
    )

    # Send to a signal for catalog info changes as well, but only once we know the transaction is committed.
    transaction.on_commit(lambda: emit_catalog_info_changed_signal(course_key))


@receiver(COURSE_CATALOG_INFO_CHANGED)
def listen_for_course_catalog_info_changed(sender, signal, **kwargs):
    """
    Publish COURSE_CATALOG_INFO_CHANGED signals onto the event bus.
    """
    get_producer().send(
        signal=COURSE_CATALOG_INFO_CHANGED, topic='course-catalog-info-changed',
        event_key_field='catalog_info.course_key', event_data={'catalog_info': kwargs['catalog_info']},
    )


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
