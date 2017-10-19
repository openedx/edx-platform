import datetime
from itertools import groupby
import logging

import attr
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.urlresolvers import reverse
from django.db.models import F, Min, Q
from django.utils.formats import dateformat, get_format



from edx_ace.recipient_resolver import RecipientResolver
from edx_ace.recipient import Recipient
from edx_ace.utils.date import serialize, deserialize

from courseware.date_summary import verified_upgrade_deadline_link, verified_upgrade_link_is_valid
from openedx.core.djangoapps.monitoring_utils import set_custom_metric, function_trace
from openedx.core.djangoapps.schedules.config import COURSE_UPDATE_WAFFLE_FLAG
from openedx.core.djangoapps.schedules.exceptions import CourseUpdateDoesNotExist
from openedx.core.djangoapps.schedules.models import Schedule, ScheduleConfig
from openedx.core.djangoapps.schedules.message_type import ScheduleMessageType
from openedx.core.djangoapps.schedules.utils import PrefixedDebugLoggerMixin
from openedx.core.djangoapps.schedules.template_context import (
    absolute_url,
    encode_url,
    encode_urls_in_dict,
    get_base_template_context
)
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration

from request_cache.middleware import request_cached
from xmodule.modulestore.django import modulestore


LOG = logging.getLogger(__name__)

DEFAULT_NUM_BINS = 24
RECURRING_NUDGE_NUM_BINS = DEFAULT_NUM_BINS
UPGRADE_REMINDER_NUM_BINS = DEFAULT_NUM_BINS
COURSE_UPDATE_NUM_BINS = DEFAULT_NUM_BINS


@attr.s
class BinnedSchedulesBaseResolver(PrefixedDebugLoggerMixin, RecipientResolver):
    """
    Starts num_bins number of async tasks, each of which sends emails to an equal group of learners.

    Arguments:
        site -- Site object that filtered Schedules will be a part of
        current_date -- datetime that will be used (with time zeroed-out) as the current date in the queries
        async_send_task -- celery task function which this resolver will call out to

    Static attributes:
        num_bins -- the int number of bins to split the users into
        enqueue_config_var -- the string field name of the config variable on ScheduleConfig to check before enqueuing
    """
    async_send_task = attr.ib()
    site = attr.ib()
    target_datetime = attr.ib()
    day_offset = attr.ib()
    bin_num = attr.ib()
    org_list = attr.ib()
    exclude_orgs = attr.ib(default=False)
    override_recipient_email = attr.ib(default=None)

    schedule_date_field = None
    num_bins = DEFAULT_NUM_BINS

    def __attrs_post_init__(self):
        # TODO: in the next refactor of this task, pass in current_datetime instead of reproducing it here
        self.current_datetime = self.target_datetime - datetime.timedelta(days=self.day_offset)

    def send(self, msg_type):
        _annotate_for_monitoring(msg_type, self.site, self.bin_num, self.target_datetime, self.day_offset)

        for (user, language, context) in self.schedules_for_bin():
            msg = msg_type.personalize(
                Recipient(
                    user.username,
                    self.override_recipient_email or user.email,
                ),
                language,
                context,
            )
            with function_trace('enqueue_send_task'):
                self.async_send_task.apply_async((self.site.id, str(msg)), retry=False)

    def get_schedules_with_target_date_by_bin_and_orgs(
        self, order_by='enrollment__user__id'
    ):
        """
        Returns Schedules with the target_date, related to Users whose id matches the bin_num, and filtered by org_list.

        Arguments:
        schedule_date_field -- string field name to query on the User's Schedule model
        current_datetime -- datetime that will be used as "right now" in the query
        target_datetime -- datetime that the User's Schedule's schedule_date_field value should fall under
        bin_num -- int for selecting the bin of Users whose id % num_bins == bin_num
        num_bin -- int specifying the number of bins to separate the Users into (default: DEFAULT_NUM_BINS)
        org_list -- list of course_org names (strings) that the returned Schedules must or must not be in (default: None)
        exclude_orgs -- boolean indicating whether the returned Schedules should exclude (True) the course_orgs in org_list
                        or strictly include (False) them (default: False)
        order_by -- string for field to sort the resulting Schedules by
        """
        target_day = _get_datetime_beginning_of_day(self.target_datetime)
        schedule_day_equals_target_day_filter = {
            'courseenrollment__schedule__{}__gte'.format(self.schedule_date_field): target_day,
            'courseenrollment__schedule__{}__lt'.format(self.schedule_date_field): target_day + datetime.timedelta(days=1),
        }
        users = User.objects.filter(
            courseenrollment__is_active=True,
            **schedule_day_equals_target_day_filter
        ).annotate(
            id_mod=F('id') % self.num_bins
        ).filter(
            id_mod=self.bin_num
        )

        schedule_day_equals_target_day_filter = {
            '{}__gte'.format(self.schedule_date_field): target_day,
            '{}__lt'.format(self.schedule_date_field): target_day + datetime.timedelta(days=1),
        }
        schedules = Schedule.objects.select_related(
            'enrollment__user__profile',
            'enrollment__course',
        ).prefetch_related(
            'enrollment__course__modes'
        ).filter(
            Q(enrollment__course__end__isnull=True) | Q(
                enrollment__course__end__gte=self.current_datetime),
            enrollment__user__in=users,
            enrollment__is_active=True,
            **schedule_day_equals_target_day_filter
        ).order_by(order_by)

        if self.org_list is not None:
            if self.exclude_orgs:
                schedules = schedules.exclude(enrollment__course__org__in=self.org_list)
            else:
                schedules = schedules.filter(enrollment__course__org__in=self.org_list)

        if "read_replica" in settings.DATABASES:
            schedules = schedules.using("read_replica")

        LOG.debug('Query = %r', schedules.query.sql_with_params())

        with function_trace('schedule_query_set_evaluation'):
            # This will run the query and cache all of the results in memory.
            num_schedules = len(schedules)

        # This should give us a sense of the volume of data being processed by each task.
        set_custom_metric('num_schedules', num_schedules)

        return schedules


class RecurringNudge(ScheduleMessageType):
    def __init__(self, day, *args, **kwargs):
        super(RecurringNudge, self).__init__(*args, **kwargs)
        self.name = "recurringnudge_day{}".format(day)


def _annotate_for_monitoring(message_type, site, bin_num, target_datetime, day_offset):
    # This identifies the type of message being sent, for example: schedules.recurring_nudge3.
    set_custom_metric('message_name', '{0}.{1}'.format(
        message_type.app_label, message_type.name))
    # The domain name of the site we are sending the message for.
    set_custom_metric('site', site.domain)
    # This is the "bin" of data being processed. We divide up the work into chunks so that we don't tie up celery
    # workers for too long. This could help us identify particular bins that are problematic.
    set_custom_metric('bin', bin_num)
    # The date we are processing data for.
    set_custom_metric('target_day', serialize(target_datetime))
    # The number of days relative to the current date to process data for.
    set_custom_metric('day_offset', day_offset)
    # A unique identifier for this batch of messages being sent.
    set_custom_metric('send_uuid', message_type.uuid)


class ScheduleStartResolver(BinnedSchedulesBaseResolver):
    """
    Send a message to all users whose schedule started at ``self.current_date`` + ``day_offset``.
    """
    log_prefix = 'Scheduled Nudge'
    schedule_date_field = 'start'
    num_bins = RECURRING_NUDGE_NUM_BINS

    def schedules_for_bin(self):

        schedules = self.get_schedules_with_target_date_by_bin_and_orgs()

        LOG.debug('Recurring Nudge: Query = %r', schedules.query.sql_with_params())

        for (user, user_schedules) in groupby(schedules, lambda s: s.enrollment.user):
            user_schedules = list(user_schedules)
            course_id_strs = [str(schedule.enrollment.course_id) for schedule in user_schedules]

            first_schedule = user_schedules[0]
            template_context = get_base_template_context(self.site)
            template_context.update({
                'student_name': user.profile.name,

                'course_name': first_schedule.enrollment.course.display_name,
                'course_url': absolute_url(self.site, reverse('course_root', args=[str(first_schedule.enrollment.course_id)])),

                # This is used by the bulk email optout policy
                'course_ids': course_id_strs,
            })

            # Information for including upsell messaging in template.
            _add_upsell_button_information_to_template_context(
                user, first_schedule, template_context)

            yield (user, first_schedule.enrollment.course.language, template_context)


def _get_datetime_beginning_of_day(dt):
    """
    Truncates hours, minutes, seconds, and microseconds to zero on given datetime.
    """
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


class UpgradeReminder(ScheduleMessageType):
    pass

class UpgradeReminderResolver(BinnedSchedulesBaseResolver):
    """
    Send a message to all users whose verified upgrade deadline is at ``self.current_date`` + ``day_offset``.
    """
    log_prefix = 'Upgrade Reminder'
    schedule_date_field = 'upgrade_deadline'
    num_bins = UPGRADE_REMINDER_NUM_BINS

    def schedules_for_bin(self):
        schedules = self.get_schedules_with_target_date_by_bin_and_orgs()

        for (user, user_schedules) in groupby(schedules, lambda s: s.enrollment.user):
            user_schedules = list(user_schedules)
            course_id_strs = [str(schedule.enrollment.course_id) for schedule in user_schedules]

            first_schedule = user_schedules[0]
            template_context = get_base_template_context(self.site)
            template_context.update({
                'student_name': user.profile.name,
                'course_links': [
                    {
                        'url': absolute_url(self.site, reverse('course_root', args=[str(s.enrollment.course_id)])),
                        'name': s.enrollment.course.display_name
                    } for s in user_schedules
                ],
                'first_course_name': first_schedule.enrollment.course.display_name,
                'cert_image': absolute_url(self.site, static('course_experience/images/verified-cert.png')),

                # This is used by the bulk email optout policy
                'course_ids': course_id_strs,
            })

            _add_upsell_button_information_to_template_context(user, first_schedule, template_context)

            yield (user, first_schedule.enrollment.course.language, template_context)


def _add_upsell_button_information_to_template_context(user, schedule, template_context):
    enrollment = schedule.enrollment
    course = enrollment.course

    verified_upgrade_link = _get_link_to_purchase_verified_certificate(
        user, schedule)
    has_verified_upgrade_link = verified_upgrade_link is not None

    if has_verified_upgrade_link:
        template_context['upsell_link'] = verified_upgrade_link
        template_context['user_schedule_upgrade_deadline_time'] = dateformat.format(
            enrollment.dynamic_upgrade_deadline,
            get_format(
                'DATE_FORMAT',
                lang=course.language,
                use_l10n=True
            )
        )

    template_context['show_upsell'] = has_verified_upgrade_link


def _get_link_to_purchase_verified_certificate(a_user, a_schedule):
    enrollment = a_schedule.enrollment
    if enrollment.dynamic_upgrade_deadline is None or not verified_upgrade_link_is_valid(enrollment):
        return None

    return verified_upgrade_deadline_link(a_user, enrollment.course)


class CourseUpdate(ScheduleMessageType):
    pass


class CourseUpdateResolver(BinnedSchedulesBaseResolver):
    """
    Send a message to all users whose schedule started at ``self.current_date`` + ``day_offset`` and the
    course has updates.
    """
    log_prefix = 'Course Update'
    schedule_date_field = 'start'
    num_bins = COURSE_UPDATE_NUM_BINS

    def schedules_for_bin(self):
        week_num = abs(self.day_offset) / 7
        schedules = self.get_schedules_with_target_date_by_bin_and_orgs(
            order_by='enrollment__course',
        )
        LOG.debug('Course Update: Query = %r', schedules.query.sql_with_params())

        for schedule in schedules:
            enrollment = schedule.enrollment
            try:
                week_summary = get_course_week_summary(
                    enrollment.course_id, week_num)
            except CourseUpdateDoesNotExist:
                continue

            user = enrollment.user
            course_id_str = str(enrollment.course_id)

            template_context = get_base_template_context(self.site)
            template_context.update({
                'student_name': user.profile.name,
                'user_personal_address': user.profile.name if user.profile.name else user.username,
                'course_name': schedule.enrollment.course.display_name,
                'course_url': absolute_url(self.site, reverse('course_root', args=[str(schedule.enrollment.course_id)])),
                'week_num': week_num,
                'week_summary': week_summary,

                # This is used by the bulk email optout policy
                'course_ids': [course_id_str],
            })

            yield (user, schedule.enrollment.course.language, template_context)


@request_cached
def get_course_week_summary(course_id, week_num):
    if COURSE_UPDATE_WAFFLE_FLAG.is_enabled(course_id):
        course = modulestore().get_course(course_id)
        return course.week_summary(week_num)
    else:
        raise CourseUpdateDoesNotExist()
