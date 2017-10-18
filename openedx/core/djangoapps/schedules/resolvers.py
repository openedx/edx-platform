import datetime
from itertools import groupby
import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.urlresolvers import reverse
from django.db.models import F, Min, Q
from django.utils.formats import dateformat, get_format


from edx_ace.recipient_resolver import RecipientResolver
from edx_ace.utils.date import serialize

from courseware.date_summary import verified_upgrade_deadline_link, verified_upgrade_link_is_valid
from openedx.core.djangoapps.monitoring_utils import set_custom_metric, function_trace
from openedx.core.djangoapps.schedules.config import COURSE_UPDATE_WAFFLE_FLAG
from openedx.core.djangoapps.schedules.exceptions import CourseUpdateDoesNotExist
from openedx.core.djangoapps.schedules.models import Schedule, ScheduleConfig
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
    num_bins = DEFAULT_NUM_BINS
    enqueue_config_var = None  # define in subclass

    def __init__(self, site, current_date, async_send_task, *args, **kwargs):
        super(BinnedSchedulesBaseResolver, self).__init__(*args, **kwargs)
        self.site = site
        self.current_date = current_date.replace(hour=0, minute=0, second=0)
        self.async_send_task = async_send_task

    def send(self, day_offset, override_recipient_email=None):
        if not self.is_enqueue_enabled():
            self.log_debug('Message queuing disabled for site %s', self.site.domain)
            return

        exclude_orgs, org_list = self.get_course_org_filter()

        target_date = self.current_date + datetime.timedelta(days=day_offset)
        self.log_debug('Target date = %s', target_date.isoformat())
        for bin in range(self.num_bins):
            task_args = (
                self.site.id, serialize(target_date), day_offset, bin, org_list, exclude_orgs, override_recipient_email,
            )
            self.log_debug('Launching task with args = %r', task_args)
            self.async_send_task.apply_async(
                task_args,
                retry=False,
            )

    def is_enqueue_enabled(self):
        if self.enqueue_config_var:
            return getattr(ScheduleConfig.current(self.site), self.enqueue_config_var)
        return False

    def get_course_org_filter(self):
        """
        Given the configuration of sites, get the list of orgs that should be included or excluded from this send.

        Returns:
             tuple: Returns a tuple (exclude_orgs, org_list). If exclude_orgs is True, then org_list is a list of the
                only orgs that should be included in this send. If exclude_orgs is False, then org_list is a list of
                orgs that should be excluded from this send. All other orgs should be included.
        """
        try:
            site_config = SiteConfiguration.objects.get(site_id=self.site.id)
            org_list = site_config.get_value('course_org_filter')
            exclude_orgs = False
            if not org_list:
                not_orgs = set()
                for other_site_config in SiteConfiguration.objects.all():
                    other = other_site_config.get_value('course_org_filter')
                    if not isinstance(other, list):
                        if other is not None:
                            not_orgs.add(other)
                    else:
                        not_orgs.update(other)
                org_list = list(not_orgs)
                exclude_orgs = True
            elif not isinstance(org_list, list):
                org_list = [org_list]
        except SiteConfiguration.DoesNotExist:
            org_list = None
            exclude_orgs = False
        finally:
            return exclude_orgs, org_list


def get_schedules_with_target_date_by_bin_and_orgs(schedule_date_field, current_datetime, target_datetime, bin_num,
                                                   num_bins=DEFAULT_NUM_BINS, org_list=None, exclude_orgs=False,
                                                   order_by='enrollment__user__id'):
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
    target_day = _get_datetime_beginning_of_day(target_datetime)
    schedule_day_equals_target_day_filter = {
        'courseenrollment__schedule__{}__gte'.format(schedule_date_field): target_day,
        'courseenrollment__schedule__{}__lt'.format(schedule_date_field): target_day + datetime.timedelta(days=1),
    }
    users = User.objects.filter(
        courseenrollment__is_active=True,
        **schedule_day_equals_target_day_filter
    ).annotate(
        id_mod=F('id') % num_bins
    ).filter(
        id_mod=bin_num
    )

    schedule_day_equals_target_day_filter = {
        '{}__gte'.format(schedule_date_field): target_day,
        '{}__lt'.format(schedule_date_field): target_day + datetime.timedelta(days=1),
    }
    schedules = Schedule.objects.select_related(
        'enrollment__user__profile',
        'enrollment__course',
    ).prefetch_related(
        'enrollment__course__modes'
    ).filter(
        Q(enrollment__course__end__isnull=True) | Q(
            enrollment__course__end__gte=current_datetime),
        enrollment__user__in=users,
        enrollment__is_active=True,
        **schedule_day_equals_target_day_filter
    ).order_by(order_by)

    if org_list is not None:
        if exclude_orgs:
            schedules = schedules.exclude(enrollment__course__org__in=org_list)
        else:
            schedules = schedules.filter(enrollment__course__org__in=org_list)

    if "read_replica" in settings.DATABASES:
        schedules = schedules.using("read_replica")

    LOG.debug('Query = %r', schedules.query.sql_with_params())

    with function_trace('schedule_query_set_evaluation'):
        # This will run the query and cache all of the results in memory.
        num_schedules = len(schedules)

    # This should give us a sense of the volume of data being processed by each task.
    set_custom_metric('num_schedules', num_schedules)

    return schedules


class ScheduleStartResolver(BinnedSchedulesBaseResolver):
    """
    Send a message to all users whose schedule started at ``self.current_date`` + ``day_offset``.
    """
    num_bins = RECURRING_NUDGE_NUM_BINS
    enqueue_config_var = 'enqueue_recurring_nudge'

    def __init__(self, *args, **kwargs):
        super(ScheduleStartResolver, self).__init__(*args, **kwargs)
        self.log_prefix = 'Scheduled Nudge'


def _recurring_nudge_schedules_for_bin(site, current_datetime, target_datetime, bin_num, org_list, exclude_orgs=False):

    schedules = get_schedules_with_target_date_by_bin_and_orgs(
        schedule_date_field='start',
        current_datetime=current_datetime,
        target_datetime=target_datetime,
        bin_num=bin_num,
        num_bins=RECURRING_NUDGE_NUM_BINS,
        org_list=org_list,
        exclude_orgs=exclude_orgs,
    )

    for (user, user_schedules) in groupby(schedules, lambda s: s.enrollment.user):
        user_schedules = list(user_schedules)
        course_id_strs = [str(schedule.enrollment.course_id)
                          for schedule in user_schedules]

        first_schedule = user_schedules[0]
        template_context = get_base_template_context(site)
        template_context.update({
            'student_name': user.profile.name,

            'course_name': first_schedule.enrollment.course.display_name,
            'course_url': absolute_url(site, reverse('course_root', args=[str(first_schedule.enrollment.course_id)])),

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


class UpgradeReminderResolver(BinnedSchedulesBaseResolver):
    """
    Send a message to all users whose verified upgrade deadline is at ``self.current_date`` + ``day_offset``.
    """
    num_bins = UPGRADE_REMINDER_NUM_BINS
    enqueue_config_var = 'enqueue_upgrade_reminder'

    def __init__(self, *args, **kwargs):
        super(UpgradeReminderResolver, self).__init__(*args, **kwargs)
        self.log_prefix = 'Upgrade Reminder'


def _upgrade_reminder_schedules_for_bin(site, current_datetime, target_datetime, bin_num, org_list, exclude_orgs=False):
    schedules = get_schedules_with_target_date_by_bin_and_orgs(
        schedule_date_field='upgrade_deadline',
        current_datetime=current_datetime,
        target_datetime=target_datetime,
        bin_num=bin_num,
        num_bins=RECURRING_NUDGE_NUM_BINS,
        org_list=org_list,
        exclude_orgs=exclude_orgs,
    )

    for (user, user_schedules) in groupby(schedules, lambda s: s.enrollment.user):
        user_schedules = list(user_schedules)
        course_id_strs = [str(schedule.enrollment.course_id) for schedule in user_schedules]

        first_schedule = user_schedules[0]
        template_context = get_base_template_context(site)
        template_context.update({
            'student_name': user.profile.name,
            'course_links': [
                {
                    'url': absolute_url(site, reverse('course_root', args=[str(s.enrollment.course_id)])),
                    'name': s.enrollment.course.display_name
                } for s in user_schedules
            ],
            'first_course_name': first_schedule.enrollment.course.display_name,
            'cert_image': absolute_url(site, static('course_experience/images/verified-cert.png')),

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


class CourseUpdateResolver(BinnedSchedulesBaseResolver):
    """
    Send a message to all users whose schedule started at ``self.current_date`` + ``day_offset`` and the
    course has updates.
    """
    num_bins = COURSE_UPDATE_NUM_BINS
    enqueue_config_var = 'enqueue_course_update'

    def __init__(self, *args, **kwargs):
        super(CourseUpdateResolver, self).__init__(*args, **kwargs)
        self.log_prefix = 'Course Update'


def _course_update_schedules_for_bin(site, current_datetime, target_datetime, day_offset, bin_num, org_list,
                                     exclude_orgs=False):
    week_num = abs(day_offset) / 7
    schedules = get_schedules_with_target_date_by_bin_and_orgs(
        schedule_date_field='start',
        current_datetime=current_datetime,
        target_datetime=target_datetime,
        bin_num=bin_num,
        num_bins=COURSE_UPDATE_NUM_BINS,
        org_list=org_list,
        exclude_orgs=exclude_orgs,
        order_by='enrollment__course',
    )

    for schedule in schedules:
        enrollment = schedule.enrollment
        try:
            week_summary = get_course_week_summary(
                enrollment.course_id, week_num)
        except CourseUpdateDoesNotExist:
            continue

        user = enrollment.user
        course_id_str = str(enrollment.course_id)

        template_context = get_base_template_context(site)
        template_context.update({
            'student_name': user.profile.name,
            'user_personal_address': user.profile.name if user.profile.name else user.username,
            'course_name': schedule.enrollment.course.display_name,
            'course_url': absolute_url(site, reverse('course_root', args=[str(schedule.enrollment.course_id)])),
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
