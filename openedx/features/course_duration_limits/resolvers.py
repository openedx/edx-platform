"""
Resolvers used to find users for course_duration_limit message
"""

from __future__ import absolute_import

import logging
from datetime import datetime, timedelta

from django.contrib.staticfiles.templatetags.staticfiles import static
from django.db.models import Q
from django.utils.timesince import timeuntil
from django.utils.translation import ugettext as _
from eventtracking import tracker

from openedx.core.djangoapps.course_modes.models import CourseMode
from courseware.date_summary import verified_upgrade_deadline_link
from lms.djangoapps.experiments.utils import stable_bucketing_hash_group
from openedx.core.djangoapps.catalog.utils import get_course_run_details
from openedx.core.djangoapps.schedules.resolvers import (
    BinnedSchedulesBaseResolver,
    InvalidContextError,
    _get_trackable_course_home_url
)
from track import segment

from .access import MAX_DURATION, MIN_DURATION, get_user_course_expiration_date
from .models import CourseDurationLimitConfig

LOG = logging.getLogger(__name__)

DEFAULT_NUM_BINS = 24
EXPIRY_REMINDER_NUM_BINS = 1
EXPIRY_REMINDER_LOG_PREFIX = 'FBE Expiry Reminder'


class ExpiryReminderResolver(BinnedSchedulesBaseResolver):
    """
    Send a message to all users whose course duration limit expiration date
    is at ``self.current_date`` + ``day_offset``.
    """
    log_prefix = EXPIRY_REMINDER_LOG_PREFIX
    schedule_date_field = 'start'
    num_bins = EXPIRY_REMINDER_NUM_BINS

    def __init__(
        self,
        async_send_task,
        site,
        course_key,
        target_datetime,
        day_offset,
        override_recipient_email=None
    ):
        access_duration = MIN_DURATION
        discovery_course_details = get_course_run_details(course_key, ['weeks_to_complete'])
        expected_weeks = discovery_course_details.get('weeks_to_complete')
        if expected_weeks:
            access_duration = timedelta(weeks=expected_weeks)

        access_duration = max(MIN_DURATION, min(MAX_DURATION, access_duration))

        self.course_key = course_key

        super(ExpiryReminderResolver, self).__init__(
            async_send_task,
            site,
            target_datetime - access_duration,
            day_offset - access_duration.days,
            0,
            override_recipient_email,
        )

    # TODO: This isn't named well, given the purpose we're using it for. That's ok for now,
    # this is just a test.
    @property
    def experience_filter(self):
        return Q(enrollment__course_id=self.course_key, enrollment__mode=CourseMode.AUDIT)

    def get_template_context(self, user, user_schedules):
        course_id_strs = []
        course_links = []
        first_valid_upsell_context = None
        first_schedule = None
        first_expiration_date = None

        self.log_info(u"Found %s schedules for %s", len(user_schedules), user.username)

        for schedule in user_schedules:
            upsell_context = _get_upsell_information_for_schedule(user, schedule)
            if not upsell_context['show_upsell']:
                self.log_info(u"No upsell available for %r", schedule.enrollment)
                continue

            if not CourseDurationLimitConfig.enabled_for_enrollment(enrollment=schedule.enrollment):
                self.log_info(u"course duration limits not enabled for %r", schedule.enrollment)
                continue

            expiration_date = get_user_course_expiration_date(user, schedule.enrollment.course)
            if expiration_date is None:
                self.log_info(u"No course expiration date for %r", schedule.enrollment.course)
                continue

            if first_valid_upsell_context is None:
                first_schedule = schedule
                first_valid_upsell_context = upsell_context
                first_expiration_date = expiration_date
            course_id_str = str(schedule.enrollment.course_id)
            course_id_strs.append(course_id_str)
            course_links.append({
                'url': _get_trackable_course_home_url(schedule.enrollment.course_id),
                'name': schedule.enrollment.course.display_name
            })

        if first_schedule is None:
            self.log_info(u'No courses eligible for upgrade for user %s.', user.username)
            raise InvalidContextError()

        # Experiment code: Skip users who are in the control bucket
        hash_bucket = stable_bucketing_hash_group('fbe_access_expiry_reminder', 2, user.username)
        properties = {
            'site': self.site.domain,  # pylint: disable=no-member
            'app_label': 'course_duration_limits',
            'nonInteraction': 1,
            'bucket': hash_bucket,
            'experiment': 'REVMI-95',
        }
        course_ids = course_id_strs
        properties['num_courses'] = len(course_ids)
        if course_ids:
            properties['course_ids'] = course_ids[:10]
            properties['primary_course_id'] = course_ids[0]

        tracking_context = {
            'host': self.site.domain,  # pylint: disable=no-member
            'path': '/',  # make up a value, in order to allow the host to be passed along.
        }
        # I wonder if the user of this event should be the recipient, as they are not the ones
        # who took an action.  Rather, the system is acting, and they are the object.
        # Admittedly that may be what 'nonInteraction' is meant to address.  But sessionization may
        # get confused by these events if they're attributed in this way, because there's no way for
        # this event to get context that would match with what the user might be doing at the moment.
        # But the events do show up in GA being joined up with existing sessions (i.e. within a half
        # hour in the past), so they don't always break sessions.  Not sure what happens after these.
        # We can put the recipient_user_id into the properties, and then export as a custom dimension.
        with tracker.get_tracker().context('course_duration_limits', tracking_context):
            segment.track(
                user_id=user.id,
                event_name='edx.bi.experiment.user.bucketed',
                properties=properties,
            )
        if hash_bucket == 0:
            raise InvalidContextError()

        context = {
            'course_links': course_links,
            'first_course_name': first_schedule.enrollment.course.display_name,
            'cert_image': static('course_experience/images/verified-cert.png'),
            'course_ids': course_id_strs,
            'first_course_expiration_date': first_expiration_date.strftime(_(u"%b. %d, %Y")),
            'time_until_expiration': timeuntil(first_expiration_date.date(), now=datetime.utcnow().date())
        }
        context.update(first_valid_upsell_context)
        return context


def _get_verified_upgrade_link(user, schedule):
    enrollment = schedule.enrollment
    if enrollment.is_active:
        return verified_upgrade_deadline_link(user, enrollment.course)


def _get_upsell_information_for_schedule(user, schedule):
    """
    Return upsell variables for inclusion in a message template being sent to this user.
    """
    template_context = {}

    verified_upgrade_link = _get_verified_upgrade_link(user, schedule)
    has_verified_upgrade_link = verified_upgrade_link is not None

    if has_verified_upgrade_link:
        template_context['upsell_link'] = verified_upgrade_link

    template_context['show_upsell'] = has_verified_upgrade_link
    return template_context
