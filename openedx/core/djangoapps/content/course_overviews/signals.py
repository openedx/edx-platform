"""
Signal handler for invalidating cached course overviews
"""


import logging

from django.db import transaction
from django.dispatch import Signal
from django.dispatch.dispatcher import receiver

from openedx.core.djangoapps.signals.signals import COURSE_CERT_DATE_CHANGE
from xmodule.modulestore.django import SignalHandler  # lint-amnesty, pylint: disable=wrong-import-order

from .models import CourseOverview

LOG = logging.getLogger(__name__)

# providing_args=["updated_course_overview", "previous_start_date"]
COURSE_START_DATE_CHANGED = Signal()
# providing_args=["updated_course_overview", "previous_self_paced"]
COURSE_PACING_CHANGED = Signal()


@receiver(SignalHandler.course_published)
def _listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been published in Studio and
    updates the corresponding CourseOverview cache entry.
    """
    try:
        previous_course_overview = CourseOverview.objects.get(id=course_key)
    except CourseOverview.DoesNotExist:
        previous_course_overview = None
    updated_course_overview = CourseOverview.load_from_module_store(course_key)
    _check_for_course_changes(previous_course_overview, updated_course_overview)


@receiver(SignalHandler.course_deleted)
def _listen_for_course_delete(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been deleted from Studio and
    invalidates the corresponding CourseOverview cache entry if one exists.
    """
    CourseOverview.objects.filter(id=course_key).delete()


def _check_for_course_changes(previous_course_overview, updated_course_overview):
    if previous_course_overview:
        _check_for_course_date_changes(previous_course_overview, updated_course_overview)
        _check_for_pacing_changes(previous_course_overview, updated_course_overview)
        _check_for_cert_availability_date_changes(previous_course_overview, updated_course_overview)


def _check_for_course_date_changes(previous_course_overview, updated_course_overview):
    if previous_course_overview.start != updated_course_overview.start:
        _log_start_date_change(previous_course_overview, updated_course_overview)
        COURSE_START_DATE_CHANGED.send(
            sender=None,
            updated_course_overview=updated_course_overview,
            previous_start_date=previous_course_overview.start,
        )


def _log_start_date_change(previous_course_overview, updated_course_overview):  # lint-amnesty, pylint: disable=missing-function-docstring
    previous_start_str = 'None'
    if previous_course_overview.start is not None:
        previous_start_str = previous_course_overview.start.isoformat()
    new_start_str = 'None'
    if updated_course_overview.start is not None:
        new_start_str = updated_course_overview.start.isoformat()
    LOG.info('Course start date changed: course={} previous={} new={}'.format(
        updated_course_overview.id,
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


def _check_for_cert_availability_date_changes(previous_course_overview, updated_course_overview):
    """ Checks if the cert available date has changed and if so, sends a COURSE_CERT_DATE_CHANGE signal"""
    if previous_course_overview.certificate_available_date != updated_course_overview.certificate_available_date:
        LOG.info(
            f"Certificate availability date for {str(updated_course_overview.id)} has changed from " +
            f"{previous_course_overview.certificate_available_date} to " +
            f"{updated_course_overview.certificate_available_date}. Sending COURSE_CERT_DATE_CHANGE signal."
        )

        def _send_course_cert_date_change_signal():
            COURSE_CERT_DATE_CHANGE.send_robust(
                sender=None,
                course_key=updated_course_overview.id,
            )

        transaction.on_commit(_send_course_cert_date_change_signal)
