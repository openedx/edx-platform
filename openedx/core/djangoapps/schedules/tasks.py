import datetime
from itertools import groupby
import logging

from celery.task import task
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db.models import F, Min, Q
from django.db.utils import DatabaseError
from django.utils.formats import dateformat, get_format
import pytz

from edx_ace import ace
from edx_ace.message import Message
from edx_ace.recipient import Recipient
from edx_ace.utils.date import deserialize
from opaque_keys.edx.keys import CourseKey

from courseware.date_summary import verified_upgrade_deadline_link, verified_upgrade_link_is_valid

from edxmako.shortcuts import marketing_link
from openedx.core.djangoapps.schedules.config import COURSE_UPDATE_WAFFLE_FLAG
from openedx.core.djangoapps.schedules.exceptions import CourseUpdateDoesNotExist
from openedx.core.djangoapps.schedules.message_type import ScheduleMessageType
from openedx.core.djangoapps.schedules.models import Schedule, ScheduleConfig
from openedx.core.djangoapps.schedules.template_context import (
    absolute_url,
    encode_url,
    encode_urls_in_dict,
    get_base_template_context
)
from request_cache.middleware import request_cached
from xmodule.modulestore.django import modulestore


LOG = logging.getLogger(__name__)


ROUTING_KEY = getattr(settings, 'ACE_ROUTING_KEY', None)
KNOWN_RETRY_ERRORS = (  # Errors we expect occasionally that could resolve on retry
    DatabaseError,
    ValidationError,
)
DEFAULT_NUM_BINS = 24
RECURRING_NUDGE_NUM_BINS = DEFAULT_NUM_BINS
UPGRADE_REMINDER_NUM_BINS = DEFAULT_NUM_BINS
COURSE_UPDATE_NUM_BINS = DEFAULT_NUM_BINS


@task(bind=True, default_retry_delay=30, routing_key=ROUTING_KEY)
def update_course_schedules(self, **kwargs):
    course_key = CourseKey.from_string(kwargs['course_id'])
    new_start_date = deserialize(kwargs['new_start_date_str'])
    new_upgrade_deadline = deserialize(kwargs['new_upgrade_deadline_str'])

    try:
        Schedule.objects.filter(enrollment__course_id=course_key).update(
            start=new_start_date,
            upgrade_deadline=new_upgrade_deadline
        )
    except Exception as exc:  # pylint: disable=broad-except
        if not isinstance(exc, KNOWN_RETRY_ERRORS):
            LOG.exception("Unexpected failure: task id: %s, kwargs=%s".format(self.request.id, kwargs))
        raise self.retry(kwargs=kwargs, exc=exc)


class RecurringNudge(ScheduleMessageType):
    def __init__(self, day, *args, **kwargs):
        super(RecurringNudge, self).__init__(*args, **kwargs)
        self.name = "recurringnudge_day{}".format(day)


@task(ignore_result=True, routing_key=ROUTING_KEY)
def _recurring_nudge_schedule_send(site_id, msg_str):
    site = Site.objects.get(pk=site_id)
    if not ScheduleConfig.current(site).deliver_recurring_nudge:
        LOG.debug('Recurring Nudge: Message delivery disabled for site %s', site.domain)
        return

    msg = Message.from_string(msg_str)
    LOG.debug('Recurring Nudge: Sending message = %s', msg_str)
    ace.send(msg)


@task(ignore_result=True, routing_key=ROUTING_KEY)
def recurring_nudge_schedule_bin(
    site_id, target_day_str, day_offset, bin_num, org_list, exclude_orgs=False, override_recipient_email=None,
):
    target_datetime = deserialize(target_day_str)
    # TODO: in the next refactor of this task, pass in current_datetime instead of reproducing it here
    current_datetime = target_datetime - datetime.timedelta(days=day_offset)
    msg_type = RecurringNudge(abs(day_offset))

    for (user, language, context) in _recurring_nudge_schedules_for_bin(
        Site.objects.get(id=site_id),
        current_datetime,
        target_datetime,
        bin_num,
        org_list,
        exclude_orgs
    ):
        msg = msg_type.personalize(
            Recipient(
                user.username,
                override_recipient_email or user.email,
            ),
            language,
            context,
        )
        _recurring_nudge_schedule_send.apply_async((site_id, str(msg)), retry=False)


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

    LOG.debug('Recurring Nudge: Query = %r', schedules.query.sql_with_params())

    for (user, user_schedules) in groupby(schedules, lambda s: s.enrollment.user):
        user_schedules = list(user_schedules)
        course_id_strs = [str(schedule.enrollment.course_id) for schedule in user_schedules]

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
        _add_upsell_button_information_to_template_context(user, first_schedule, template_context)

        yield (user, first_schedule.enrollment.course.language, template_context)


class UpgradeReminder(ScheduleMessageType):
    pass


@task(ignore_result=True, routing_key=ROUTING_KEY)
def upgrade_reminder_schedule_bin(
    site_id, target_day_str, day_offset, bin_num, org_list, exclude_orgs=False, override_recipient_email=None,
):
    target_datetime = deserialize(target_day_str)
    # TODO: in the next refactor of this task, pass in current_datetime instead of reproducing it here
    current_datetime = target_datetime - datetime.timedelta(days=day_offset)
    msg_type = UpgradeReminder()

    for (user, language, context) in _upgrade_reminder_schedules_for_bin(
        Site.objects.get(id=site_id),
        current_datetime,
        target_datetime,
        bin_num,
        org_list,
        exclude_orgs
    ):
        msg = msg_type.personalize(
            Recipient(
                user.username,
                override_recipient_email or user.email,
            ),
            language,
            context,
        )
        _upgrade_reminder_schedule_send.apply_async((site_id, str(msg)), retry=False)


@task(ignore_result=True, routing_key=ROUTING_KEY)
def _upgrade_reminder_schedule_send(site_id, msg_str):
    site = Site.objects.get(pk=site_id)
    if not ScheduleConfig.current(site).deliver_upgrade_reminder:
        return

    msg = Message.from_string(msg_str)
    ace.send(msg)


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

    LOG.debug('Upgrade Reminder: Query = %r', schedules.query.sql_with_params())

    for schedule in schedules:
        enrollment = schedule.enrollment
        user = enrollment.user

        course_id_str = str(enrollment.course_id)

        # TODO: group by schedule and user like recurring nudge
        course_id_strs = [course_id_str]
        first_schedule = schedule

        template_context = get_base_template_context(site)
        template_context.update({
            'student_name': user.profile.name,
            'user_personal_address': user.profile.name if user.profile.name else user.username,

            'course_name': first_schedule.enrollment.course.display_name,
            'course_url': absolute_url(site, reverse('course_root', args=[str(first_schedule.enrollment.course_id)])),

            # This is used by the bulk email optout policy
            'course_ids': course_id_strs,
            'cert_image': absolute_url(site, static('course_experience/images/verified-cert.png')),
        })

        _add_upsell_button_information_to_template_context(user, first_schedule, template_context)

        yield (user, first_schedule.enrollment.course.language, template_context)


class CourseUpdate(ScheduleMessageType):
    pass


@task(ignore_result=True, routing_key=ROUTING_KEY)
def course_update_schedule_bin(
    site_id, target_day_str, day_offset, bin_num, org_list, exclude_orgs=False, override_recipient_email=None,
):
    target_datetime = deserialize(target_day_str)
    # TODO: in the next refactor of this task, pass in current_datetime instead of reproducing it here
    current_datetime = target_datetime - datetime.timedelta(days=day_offset)
    msg_type = CourseUpdate()

    for (user, language, context) in _course_update_schedules_for_bin(
        Site.objects.get(id=site_id),
        current_datetime,
        target_datetime,
        day_offset,
        bin_num,
        org_list,
        exclude_orgs
    ):
        msg = msg_type.personalize(
            Recipient(
                user.username,
                override_recipient_email or user.email,
            ),
            language,
            context,
        )
        _course_update_schedule_send.apply_async((site_id, str(msg)), retry=False)


@task(ignore_result=True, routing_key=ROUTING_KEY)
def _course_update_schedule_send(site_id, msg_str):
    site = Site.objects.get(pk=site_id)
    if not ScheduleConfig.current(site).deliver_course_update:
        return

    msg = Message.from_string(msg_str)
    ace.send(msg)


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

    LOG.debug('Course Update: Query = %r', schedules.query.sql_with_params())

    for schedule in schedules:
        enrollment = schedule.enrollment
        try:
            week_summary = get_course_week_summary(enrollment.course_id, week_num)
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
        Q(enrollment__course__end__isnull=True) | Q(enrollment__course__end__gte=current_datetime),
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

    return schedules


def _add_upsell_button_information_to_template_context(user, schedule, template_context):
    enrollment = schedule.enrollment
    course = enrollment.course

    verified_upgrade_link = _get_link_to_purchase_verified_certificate(user, schedule)
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


def _get_datetime_beginning_of_day(dt):
    """
    Truncates hours, minutes, seconds, and microseconds to zero on given datetime.
    """
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)
