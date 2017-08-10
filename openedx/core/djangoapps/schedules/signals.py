import datetime
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from course_modes.models import CourseMode
from courseware.models import CourseScheduleConfiguration
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import CourseEnrollment
from .models import Schedule

log = logging.getLogger(__name__)


def _get_upgrade_deadline(schedule_config, enrollment):
    """ Returns the upgrade deadline for the given enrollment.

    The deadline is determined based on the following data (in priority order):
        1. Course run-specific schedule configuration (CourseScheduleConfiguration)
        2. Verified course mode expiration
    """
    course_key = enrollment.course_id
    upgrade_deadline = datetime.date.max

    try:
        verified_mode = CourseMode.verified_mode_for_course(course_key)
        if verified_mode:
            upgrade_deadline = verified_mode.expiration_datetime
    except CourseMode.DoesNotExist:
        pass

    delta = schedule_config.verified_upgrade_deadline_days

    course_overview = CourseOverview.get_from_id(course_key)

    # This represents the first date at which the learner can access the content. This will be the latter of
    # either the enrollment date or the course's start date.
    content_availability_date = max(enrollment.created, course_overview.start)
    cav_based_deadline = content_availability_date + datetime.timedelta(days=delta)

    # The content availability-based deadline should never occur after the verified mode's
    # expiration date, if one is set.
    return min(upgrade_deadline, cav_based_deadline)


@receiver(post_save, sender=CourseEnrollment, dispatch_uid='create_schedule_for_enrollment')
def create_schedule(sender, **kwargs):
    enrollment = kwargs['instance']
    schedule_config = CourseScheduleConfiguration.current(enrollment.course_id)
    if schedule_config.enabled and kwargs['created']:
        upgrade_deadline = _get_upgrade_deadline(schedule_config, enrollment)
        Schedule.objects.create(enrollment=enrollment, start=timezone.now(), upgrade_deadline=upgrade_deadline)
