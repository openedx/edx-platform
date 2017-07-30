"""
Schedule related signal handlers.
"""
import datetime
import logging

from django.dispatch import receiver
from django.utils import timezone

from openedx.core.djangoapps.schedules.models import Schedule
from student.models import ENROLL_STATUS_CHANGE, EnrollStatusChange, CourseEnrollment

log = logging.getLogger(__name__)


@receiver(ENROLL_STATUS_CHANGE)
def create_schedule_for_self_paced_enrollment(sender, event=None, user=None, course_id=None, **kwargs):
    log.info('Running schedule signal handler')
    if event != EnrollStatusChange.enroll:
        return

    log.info('Creating schedule for new enrollment')
    enrollment = CourseEnrollment.get_enrollment(user, course_id)
    schedule = Schedule(
        enrollment=enrollment,
        active=True,
        start=timezone.now(),
        upgrade_deadline=timezone.now() + datetime.timedelta(days=21)
    )
    schedule.save()
