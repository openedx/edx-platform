import datetime
import logging
import random

import analytics
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from course_modes.models import CourseMode
from courseware.models import (
    CourseDynamicUpgradeDeadlineConfiguration,
    DynamicUpgradeDeadlineConfiguration,
    OrgDynamicUpgradeDeadlineConfiguration
)
from edx_ace.utils import date
from openedx.core.djangoapps.schedules.models import ScheduleExperience
from openedx.core.djangoapps.schedules.content_highlights import course_has_highlights
from openedx.core.djangoapps.signals.signals import COURSE_START_DATE_CHANGED
from openedx.core.djangoapps.theming.helpers import get_current_site
from student.models import CourseEnrollment
from .config import CREATE_SCHEDULE_WAFFLE_FLAG
from .models import Schedule, ScheduleConfig
from .tasks import update_course_schedules


log = logging.getLogger(__name__)


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
        and not CREATE_SCHEDULE_WAFFLE_FLAG.is_enabled(enrollment.course_id)
    ):
        log.debug('Schedules: Creation not enabled for this course or for this site')
        return

    if not enrollment.course_overview.self_paced:
        log.debug('Schedules: Creation only enabled for self-paced courses')
        return

    # This represents the first date at which the learner can access the content. This will be the latter of
    # either the enrollment date or the course's start date.
    content_availability_date = max(enrollment.created, enrollment.course_overview.start)

    upgrade_deadline = _calculate_upgrade_deadline(enrollment.course_id, content_availability_date)

    if course_has_highlights(enrollment.course_id):
        experience_type = ScheduleExperience.EXPERIENCES.course_updates
    else:
        experience_type = ScheduleExperience.EXPERIENCES.default

    if _should_randomly_suppress_schedule_creation(
        schedule_config,
        enrollment,
        upgrade_deadline,
        experience_type,
        content_availability_date,
    ):
        return

    schedule = Schedule.objects.create(
        enrollment=enrollment,
        start=content_availability_date,
        upgrade_deadline=upgrade_deadline
    )

    ScheduleExperience(schedule=schedule, experience_type=experience_type).save()

    log.debug('Schedules: created a new schedule starting at %s with an upgrade deadline of %s and experience type: %s',
              content_availability_date, upgrade_deadline, ScheduleExperience.EXPERIENCES[experience_type])


@receiver(COURSE_START_DATE_CHANGED, dispatch_uid="update_schedules_on_course_start_changed")
def update_schedules_on_course_start_changed(sender, updated_course_overview, previous_start_date, **kwargs):
    """
    Updates all course schedules if course hasn't started yet and
    the updated start date is still in the future.
    """
    upgrade_deadline = _calculate_upgrade_deadline(
        updated_course_overview.id,
        content_availability_date=updated_course_overview.start,
    )
    update_course_schedules.apply_async(
        kwargs=dict(
            course_id=unicode(updated_course_overview.id),
            new_start_date_str=date.serialize(updated_course_overview.start),
            new_upgrade_deadline_str=date.serialize(upgrade_deadline),
        ),
    )


def _calculate_upgrade_deadline(course_id, content_availability_date):
    upgrade_deadline = None

    delta = _get_upgrade_deadline_delta_setting(course_id)
    if delta is not None:
        upgrade_deadline = content_availability_date + datetime.timedelta(days=delta)
        if upgrade_deadline is not None:
            # The content availability-based deadline should never occur
            # after the verified mode's expiration date, if one is set.
            try:
                verified_mode = CourseMode.verified_mode_for_course(course_id)
            except CourseMode.DoesNotExist:
                pass
            else:
                if verified_mode:
                    course_mode_upgrade_deadline = verified_mode.expiration_datetime
                    if course_mode_upgrade_deadline is not None:
                        upgrade_deadline = min(upgrade_deadline, course_mode_upgrade_deadline)

    return upgrade_deadline


def _get_upgrade_deadline_delta_setting(course_id):
    delta = None

    global_config = DynamicUpgradeDeadlineConfiguration.current()
    if global_config.enabled:
        # Use the default from this model whether or not the feature is enabled
        delta = global_config.deadline_days

    # Check if the org has a deadline
    org_config = OrgDynamicUpgradeDeadlineConfiguration.current(course_id.org)
    if org_config.opted_in():
        delta = org_config.deadline_days
    elif org_config.opted_out():
        delta = None

    # Check if the course has a deadline
    course_config = CourseDynamicUpgradeDeadlineConfiguration.current(course_id)
    if course_config.opted_in():
        delta = course_config.deadline_days
    elif course_config.opted_out():
        delta = None

    return delta


def _should_randomly_suppress_schedule_creation(
    schedule_config,
    enrollment,
    upgrade_deadline,
    experience_type,
    content_availability_date,
):
    # The hold back ratio is always between 0 and 1. A value of 0 indicates that schedules should be created for all
    # schedules. A value of 1 indicates that no schedules should be created for any enrollments. A value of 0.2 would
    # mean that 20% of enrollments should *not* be given schedules.

    # This allows us to measure the impact of the dynamic schedule experience by comparing this "control" group that
    # does not receive any of benefits of the feature against the group that does.
    if random.random() < schedule_config.hold_back_ratio:
        log.debug('Schedules: Enrollment held back from dynamic schedule experiences.')
        upgrade_deadline_str = None
        if upgrade_deadline:
            upgrade_deadline_str = upgrade_deadline.isoformat()
        analytics.track(
            'edx.bi.schedule.suppressed',
            {
                'user_id': enrollment.user.id,
                'course_id': unicode(enrollment.course_id),
                'experience_type': experience_type,
                'upgrade_deadline': upgrade_deadline_str,
                'content_availability_date': content_availability_date.isoformat(),
            }
        )
        return True

    return False
