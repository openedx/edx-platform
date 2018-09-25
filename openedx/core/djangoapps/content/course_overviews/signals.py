"""
Signal handler for invalidating cached course overviews
"""
import logging

from django.dispatch import Signal
from django.dispatch.dispatcher import receiver

from .models import CourseOverview
from xmodule.modulestore.django import SignalHandler

LOG = logging.getLogger(__name__)


COURSE_START_DATE_CHANGED = Signal(providing_args=["updated_course_overview", "previous_start_date"])
COURSE_PACING_CHANGED = Signal(providing_args=["updated_course_overview", "previous_self_paced"])


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
        _log_course_date_change(
            previous_course_overview.start,
            updated_course_overview.start,
            'Course start date changed',
        )
        COURSE_START_DATE_CHANGED.send(
            sender=None,
            updated_course_overview=updated_course_overview,
            previous_start_date=previous_course_overview.start,
        )
    if previous_course_overview.end != updated_course_overview.end:
        _log_course_date_change(
            previous_course_overview.end,
            updated_course_overview.end,
            'Course end date changed',
        )


def _log_course_date_change(previous_course_date, updated_course_date, log_mesg):
    previous_start_str = 'None'
    if previous_course_date is not None:
        previous_start_str = previous_course_date.isoformat()
    new_start_str = 'None'
    if updated_course_date is not None:
        new_start_str = updated_course_date.isoformat()
    LOG.info('{0}: course={1} previous={2} new={3}'.format(
        log_mesg,
        updated_course_date.id,
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
