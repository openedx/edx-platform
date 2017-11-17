"""
Signal handler for invalidating cached course overviews
"""
import logging

from django.dispatch.dispatcher import receiver

from .models import CourseOverview
from openedx.core.djangoapps.signals.signals import COURSE_PACING_CHANGED, COURSE_START_DATE_CHANGED
from xmodule.modulestore.django import SignalHandler

LOG = logging.getLogger(__name__)


@receiver(SignalHandler.course_published)
def _listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been published in Studio and
    updates the corresponding CourseOverview cache entry.
    """
    previous_course_overview = CourseOverview.get_from_ids_if_exists([course_key]).get(course_key)
    updated_course_overview = CourseOverview.load_from_module_store(course_key)
    _check_for_course_changes(previous_course_overview, updated_course_overview)


@receiver(SignalHandler.course_deleted)
def _listen_for_course_delete(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been deleted from Studio and
    invalidates the corresponding CourseOverview cache entry if one exists.
    """
    CourseOverview.objects.filter(id=course_key).delete()
    # import CourseAboutSearchIndexer inline due to cyclic import
    from cms.djangoapps.contentstore.courseware_index import CourseAboutSearchIndexer
    # Delete course entry from Course About Search_index
    CourseAboutSearchIndexer.remove_deleted_items(course_key)


def _check_for_course_changes(previous_course_overview, updated_course_overview):
    if previous_course_overview:
        _check_for_course_date_changes(previous_course_overview, updated_course_overview)
        _check_for_pacing_changes(previous_course_overview, updated_course_overview)


def _check_for_course_date_changes(previous_course_overview, updated_course_overview):
    if previous_course_overview.start != updated_course_overview.start:
        _log_start_date_change(previous_course_overview, updated_course_overview)
        COURSE_START_DATE_CHANGED.send(
            sender=None,
            updated_course_overview=updated_course_overview,
            previous_start_date=previous_course_overview.start,
        )


def _log_start_date_change(previous_course_overview, updated_course_overview):
    previous_start_str = 'None'
    if previous_course_overview.start is not None:
        previous_start_str = previous_course_overview.start.isoformat()
    new_start_str = 'None'
    if updated_course_overview.start is not None:
        new_start_str = updated_course_overview.start.isoformat()
    LOG.info('Course start date changed: previous={0} new={1}'.format(
        previous_start_str,
        new_start_str,
    ))


def _check_for_pacing_changes(previous_course_overview, updated_course_overview):
    if previous_course_overview.self_paced != updated_course_overview.self_paced:
        COURSE_PACING_CHANGED.send(
            sender=None,
            updated_course_overview=updated_course_overview,
            previous_self_paced=previous_course_overview.self_paced,
        )
