import datetime
from itertools import groupby
import logging

from celery.task import task
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db.models import F, Min, Prefetch
from django.db.utils import DatabaseError

from edx_ace import ace
from edx_ace.message import Message
from edx_ace.recipient import Recipient
from edx_ace.utils.date import deserialize
from opaque_keys.edx.keys import CourseKey

from course_modes.models import CourseMode
from edxmako.shortcuts import marketing_link
from openedx.core.djangoapps.schedules.message_type import ScheduleMessageType
from openedx.core.djangoapps.schedules.models import Schedule, ScheduleConfig
from openedx.core.djangoapps.schedules.template_context import (
    absolute_url,
    encode_url,
    encode_urls_in_dict,
    get_base_template_context
)
from openedx.core.djangoapps.user_api.models import UserPreference


LOG = logging.getLogger(__name__)


ROUTING_KEY = getattr(settings, 'ACE_ROUTING_KEY', None)
KNOWN_RETRY_ERRORS = (  # Errors we expect occasionally that could resolve on retry
    DatabaseError,
    ValidationError,
)
DEFAULT_NUM_BINS = 24
RECURRING_NUDGE_NUM_BINS = DEFAULT_NUM_BINS
UPGRADE_REMINDER_NUM_BINS = DEFAULT_NUM_BINS


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


# TODO: delete once recurring_nudge_schedule_bin is fully rolled out
@task(ignore_result=True, routing_key=ROUTING_KEY)
def recurring_nudge_schedule_hour(
    site_id, day, target_hour_str, org_list, exclude_orgs=False, override_recipient_email=None,
):
    target_hour = deserialize(target_hour_str)
    msg_type = RecurringNudge(day)

    for (user, language, context) in _recurring_nudge_schedules_for_hour(target_hour, org_list, exclude_orgs):
        msg = msg_type.personalize(
            Recipient(
                user.username,
                override_recipient_email or user.email,
            ),
            language,
            context,
        )
        _recurring_nudge_schedule_send.apply_async((site_id, str(msg)), retry=False)


@task(ignore_result=True, routing_key=ROUTING_KEY)
def _recurring_nudge_schedule_send(site_id, msg_str):
    site = Site.objects.get(pk=site_id)
    if not ScheduleConfig.current(site).deliver_recurring_nudge:
        LOG.debug('Recurring Nudge: Message delivery disabled for site %s', site.domain)
        return

    msg = Message.from_string(msg_str)
    LOG.debug('Recurring Nudge: Sending message = %s', msg_str)
    ace.send(msg)


# TODO: delete once _recurring_nudge_schedules_for_bin is fully rolled out
def _recurring_nudge_schedules_for_hour(target_hour, org_list, exclude_orgs=False):
    beginning_of_day = target_hour.replace(hour=0, minute=0, second=0)
    users = User.objects.filter(
        courseenrollment__schedule__start__gte=beginning_of_day,
        courseenrollment__schedule__start__lt=beginning_of_day + datetime.timedelta(days=1),
        courseenrollment__is_active=True,
    ).annotate(
        first_schedule=Min('courseenrollment__schedule__start')
    ).filter(
        first_schedule__gte=target_hour,
        first_schedule__lt=target_hour + datetime.timedelta(minutes=60)
    )

    schedules = Schedule.objects.select_related(
        'enrollment__user__profile',
        'enrollment__course',
    ).filter(
        enrollment__user__in=users,
        start__gte=beginning_of_day,
        start__lt=beginning_of_day + datetime.timedelta(days=1),
        enrollment__is_active=True,
    ).order_by('enrollment__user__id')

    if org_list is not None:
        if exclude_orgs:
            schedules = schedules.exclude(enrollment__course__org__in=org_list)
        else:
            schedules = schedules.filter(enrollment__course__org__in=org_list)

    if "read_replica" in settings.DATABASES:
        schedules = schedules.using("read_replica")

    LOG.debug('Scheduled Nudge: Query = %r', schedules.query.sql_with_params())

    dashboard_relative_url = reverse('dashboard')

    for (user, user_schedules) in groupby(schedules, lambda s: s.enrollment.user):
        user_schedules = list(user_schedules)
        course_id_strs = [str(schedule.enrollment.course_id) for schedule in user_schedules]

        first_schedule = user_schedules[0]
        template_context = {
            'student_name': user.profile.name,

            'course_name': first_schedule.enrollment.course.display_name,
            'course_url': absolute_url(reverse('course_root', args=[str(first_schedule.enrollment.course_id)])),

            # This is used by the bulk email optout policy
            'course_ids': course_id_strs,

            # Platform information
            'homepage_url': encode_url(marketing_link('ROOT')),
            'dashboard_url': absolute_url(dashboard_relative_url),
            'template_revision': settings.EDX_PLATFORM_REVISION,
            'platform_name': settings.PLATFORM_NAME,
            'contact_mailing_address': settings.CONTACT_MAILING_ADDRESS,
            'social_media_urls': encode_urls_in_dict(getattr(settings, 'SOCIAL_MEDIA_FOOTER_URLS', {})),
            'mobile_store_urls': encode_urls_in_dict(getattr(settings, 'MOBILE_STORE_URLS', {})),
        }
        yield (user, first_schedule.enrollment.course.language, template_context)


@task(ignore_result=True, routing_key=ROUTING_KEY)
def recurring_nudge_schedule_bin(
    site_id, target_day_str, day_offset, bin_num, org_list, exclude_orgs=False, override_recipient_email=None,
):
    target_day = deserialize(target_day_str)
    msg_type = RecurringNudge(abs(day_offset))

    for (user, language, context) in _recurring_nudge_schedules_for_bin(target_day, bin_num, org_list, exclude_orgs):
        msg = msg_type.personalize(
            Recipient(
                user.username,
                override_recipient_email or user.email,
            ),
            language,
            context,
        )
        _recurring_nudge_schedule_send.apply_async((site_id, str(msg)), retry=False)


def _recurring_nudge_schedules_for_bin(target_day, bin_num, org_list, exclude_orgs=False):
    beginning_of_day = target_day.replace(hour=0, minute=0, second=0)
    users = User.objects.filter(
        courseenrollment__schedule__start__gte=beginning_of_day,
        courseenrollment__schedule__start__lt=beginning_of_day + datetime.timedelta(days=1),
        courseenrollment__is_active=True,
    ).annotate(
        first_schedule=Min('courseenrollment__schedule__start')
    ).annotate(
        id_mod=F('id') % RECURRING_NUDGE_NUM_BINS
    ).filter(
        id_mod=bin_num
    )

    schedules = Schedule.objects.select_related(
        'enrollment__user__profile',
        'enrollment__course',
    ).filter(
        enrollment__user__in=users,
        start__gte=beginning_of_day,
        start__lt=beginning_of_day + datetime.timedelta(days=1),
        enrollment__is_active=True,
    ).order_by('enrollment__user__id')

    if org_list is not None:
        if exclude_orgs:
            schedules = schedules.exclude(enrollment__course__org__in=org_list)
        else:
            schedules = schedules.filter(enrollment__course__org__in=org_list)

    if "read_replica" in settings.DATABASES:
        schedules = schedules.using("read_replica")

    for (user, user_schedules) in groupby(schedules, lambda s: s.enrollment.user):
        user_schedules = list(user_schedules)
        course_id_strs = [str(schedule.enrollment.course_id) for schedule in user_schedules]

        first_schedule = user_schedules[0]
        template_context = get_base_template_context()
        template_context.update({
            'student_name': user.profile.name,

            'course_name': first_schedule.enrollment.course.display_name,
            'course_url': absolute_url(reverse('course_root', args=[str(first_schedule.enrollment.course_id)])),

            # This is used by the bulk email optout policy
            'course_ids': course_id_strs,
        })
        yield (user, first_schedule.enrollment.course.language, template_context)


class UpgradeReminder(ScheduleMessageType):
    def __init__(self, day, *args, **kwargs):
        super(UpgradeReminder, self).__init__(*args, **kwargs)
        self.name = "upgradereminder".format(day)


@task(ignore_result=True, routing_key=ROUTING_KEY)
def upgrade_reminder_schedule_bin(
    site_id, target_day_str, day_offset, bin_num, org_list, exclude_orgs=False, override_recipient_email=None,
):
    target_day = deserialize(target_day_str)
    msg_type = UpgradeReminder(abs(day_offset))

    for (user, language, context) in _upgrade_reminder_schedules_for_bin(target_day, bin_num, org_list, exclude_orgs):
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


def _upgrade_reminder_schedules_for_bin(target_day, bin_num, org_list, exclude_orgs=False):
    schedules = Schedule.objects.select_related(
        'enrollment__user__profile',
        'enrollment__course',
    ).prefetch_related(
        Prefetch(
            'enrollment__course__modes',
            queryset=CourseMode.objects.filter(mode_slug=CourseMode.VERIFIED),
            to_attr='verified_modes'
        ),
        Prefetch(
            'enrollment__user__preferences',
            queryset=UserPreference.objects.filter(key='time_zone'),
            to_attr='tzprefs'
        ),
    ).annotate(
        id_mod=F('enrollment__user__id') % UPGRADE_REMINDER_NUM_BINS
    ).filter(
        id_mod=bin_num
    ).filter(
        upgrade_deadline__year=target_day.year,
        upgrade_deadline__month=target_day.month,
        upgrade_deadline__day=target_day.day,
    )

    if "read_replica" in settings.DATABASES:
        schedules = schedules.using("read_replica")

    for schedule in schedules:
        enrollment = schedule.enrollment
        user = enrollment.user

        course_id_str = str(enrollment.course_id)
        course = enrollment.course

        # TODO: group by schedule and user like recurring nudge
        course_id_strs = [course_id_str]
        first_schedule = schedule

        template_context = get_base_template_context()
        template_context.update({
            'student_name': user.profile.name,
            'user_personal_address': user.profile.name if user.profile.name else user.username,
            'user_schedule_upgrade_deadline_time': schedule.upgrade_deadline,

            'course_name': first_schedule.enrollment.course.display_name,
            'course_url': absolute_url(reverse('course_root', args=[str(first_schedule.enrollment.course_id)])),

            # This is used by the bulk email optout policy
            'course_ids': course_id_strs,
        })

        yield (user, course.language, template_context)
