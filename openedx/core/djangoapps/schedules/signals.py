import datetime
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from course_modes.models import CourseMode
from courseware.models import DynamicUpgradeDeadlineConfiguration, CourseDynamicUpgradeDeadlineConfiguration
from openedx.core.djangoapps.theming.helpers import get_current_site
from openedx.core.djangoapps.waffle_utils import WaffleFlagNamespace, CourseWaffleFlag
from student.models import CourseEnrollment
from .models import Schedule, ScheduleConfig

log = logging.getLogger(__name__)


SCHEDULE_WAFFLE_FLAG = CourseWaffleFlag(
    waffle_namespace=WaffleFlagNamespace('schedules'),
    flag_name='create_schedules_for_course',
    flag_undefined_default=False
)


@receiver(post_save, sender=CourseEnrollment, dispatch_uid='create_schedule_for_enrollment')
def create_schedule(sender, **kwargs):
    if not kwargs['created']:
        # only create schedules when enrollment records are created
        return

    current_site = get_current_site()
    if current_site is None:
        log.debug('Schedules: No current site')
        return

    enrollment = kwargs['instance']
    schedule_config = ScheduleConfig.current(current_site)
    if (
        not schedule_config.create_schedules
        and not SCHEDULE_WAFFLE_FLAG.is_enabled(enrollment.course_id)
    ):
        log.debug('Schedules: Creation not enabled for this course or for this site')
        return

    if not enrollment.course_overview.self_paced:
        log.debug('Schedules: Creation only enabled for self-paced courses')
        return

    delta = None
    global_config = DynamicUpgradeDeadlineConfiguration.current()
    if global_config.enabled:
        # Use the default from this model whether or not the feature is enabled
        delta = global_config.deadline_days

    # Check if the course has a deadline override
    course_config = CourseDynamicUpgradeDeadlineConfiguration.current(enrollment.course_id)
    if course_config.enabled:
        delta = course_config.deadline_days

    upgrade_deadline = None

    # This represents the first date at which the learner can access the content. This will be the latter of
    # either the enrollment date or the course's start date.
    content_availability_date = max(enrollment.created, enrollment.course_overview.start)

    if delta is not None:
        upgrade_deadline = content_availability_date + datetime.timedelta(days=delta)

        course_upgrade_deadline = None
        try:
            verified_mode = CourseMode.verified_mode_for_course(enrollment.course_id)
        except CourseMode.DoesNotExist:
            pass
        else:
            if verified_mode:
                course_upgrade_deadline = verified_mode.expiration_datetime

        if course_upgrade_deadline is not None and upgrade_deadline is not None:
            # The content availability-based deadline should never occur after the verified mode's
            # expiration date, if one is set.
            upgrade_deadline = min(upgrade_deadline, course_upgrade_deadline)

    Schedule.objects.create(
        enrollment=enrollment,
        start=content_availability_date,
        upgrade_deadline=upgrade_deadline
    )

    log.debug('Schedules: created a new schedule starting at %s with an upgrade deadline of %s',
              content_availability_date, upgrade_deadline)
