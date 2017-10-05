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
from django.db.models import F, Min
from django.db.utils import DatabaseError
from django.utils.formats import dateformat, get_format

from edx_ace import ace
from edx_ace.message import Message
from edx_ace.recipient import Recipient
from edx_ace.utils.date import deserialize
from opaque_keys.edx.keys import CourseKey

from edxmako.shortcuts import marketing_link
from openedx.core.djangoapps.schedules.message_type import ScheduleMessageType
from openedx.core.djangoapps.schedules.models import Schedule, ScheduleConfig
from openedx.core.djangoapps.schedules.template_context import (
    absolute_url,
    encode_url,
    encode_urls_in_dict,
    get_base_template_context
)


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
    schedules = get_schedules_with_target_date_by_bin_and_orgs(
        schedule_date_field='start',
        target_date=beginning_of_day,
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
    pass


@task(ignore_result=True, routing_key=ROUTING_KEY)
def upgrade_reminder_schedule_bin(
    site_id, target_day_str, day_offset, bin_num, org_list, exclude_orgs=False, override_recipient_email=None,
):
    target_day = deserialize(target_day_str)
    msg_type = UpgradeReminder()

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
    beginning_of_day = target_day.replace(hour=0, minute=0, second=0)

    schedules = get_schedules_with_target_date_by_bin_and_orgs(
        schedule_date_field='upgrade_deadline',
        target_date=beginning_of_day,
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

        template_context = get_base_template_context()
        template_context.update({
            'student_name': user.profile.name,
            'user_personal_address': user.profile.name if user.profile.name else user.username,
            'user_schedule_upgrade_deadline_time': dateformat.format(
                schedule.upgrade_deadline,
                get_format(
                    'DATE_FORMAT',
                    lang=first_schedule.enrollment.course.language,
                    use_l10n=True
                )
            ),

            'course_name': first_schedule.enrollment.course.display_name,
            'course_url': absolute_url(reverse('course_root', args=[str(first_schedule.enrollment.course_id)])),

            # This is used by the bulk email optout policy
            'course_ids': course_id_strs,
            'cert_image': absolute_url(static('course_experience/images/verified-cert.png')),
        })

        yield (user, first_schedule.enrollment.course.language, template_context)


def get_schedules_with_target_date_by_bin_and_orgs(schedule_date_field, target_date, bin_num, num_bins=DEFAULT_NUM_BINS,
                                                   org_list=None, exclude_orgs=False):
    """
    Returns Schedules with the target_date, related to Users whose id matches the bin_num, and filtered by org_list.

    Arguments:
    schedule_date_field -- string field name to query on the User's Schedule model
    target_date -- datetime day (with zeroed-out time) that the User's Schedule's schedule_date_field value should fall
                   under
    bin_num -- int for selecting the bin of Users whose id % num_bins == bin_num
    num_bin -- int specifying the number of bins to separate the Users into (default: DEFAULT_NUM_BINS)
    org_list -- list of course_org names (strings) that the returned Schedules must or must not be in (default: None)
    exclude_orgs -- boolean indicating whether the returned Schedules should exclude (True) the course_orgs in org_list
                    or strictly include (False) them (default: False)
    """
    schedule_date_equals_target_date_filter = {
        'courseenrollment__schedule__{}__gte'.format(schedule_date_field): target_date,
        'courseenrollment__schedule__{}__lt'.format(schedule_date_field): target_date + datetime.timedelta(days=1),
    }
    users = User.objects.filter(
        courseenrollment__is_active=True,
        **schedule_date_equals_target_date_filter
    ).annotate(
        id_mod=F('id') % num_bins
    ).filter(
        id_mod=bin_num
    )

    schedule_date_equals_target_date_filter = {
        '{}__gte'.format(schedule_date_field): target_date,
        '{}__lt'.format(schedule_date_field): target_date + datetime.timedelta(days=1),
    }
    schedules = Schedule.objects.select_related(
        'enrollment__user__profile',
        'enrollment__course',
    ).filter(
        enrollment__user__in=users,
        enrollment__is_active=True,
        **schedule_date_equals_target_date_filter
    ).order_by('enrollment__user__id')

    if org_list is not None:
        if exclude_orgs:
            schedules = schedules.exclude(enrollment__course__org__in=org_list)
        else:
            schedules = schedules.filter(enrollment__course__org__in=org_list)

    if "read_replica" in settings.DATABASES:
        schedules = schedules.using("read_replica")

    return schedules
