import datetime
from itertools import groupby
import logging
from urlparse import urlparse

from celery.task import task
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db.models import Min
from django.db.utils import DatabaseError
from django.utils.http import urlquote

from edx_ace import ace
from edx_ace.message import Message
from edx_ace.recipient import Recipient
from edx_ace.utils.date import deserialize
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.schedules.message_type import ScheduleMessageType
from openedx.core.djangoapps.schedules.models import Schedule, ScheduleConfig
from openedx.core.djangoapps.schedules.template_context import absolute_url, get_base_template_context


LOG = logging.getLogger(__name__)


ROUTING_KEY = getattr(settings, 'ACE_ROUTING_KEY', None)
KNOWN_RETRY_ERRORS = (  # Errors we expect occasionally that could resolve on retry
    DatabaseError,
    ValidationError,
)


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
        template_context = get_base_template_context()
        template_context.update({
            'student_name': user.profile.name,

            'course_name': first_schedule.enrollment.course.display_name,
            'course_url': absolute_url(reverse('course_root', args=[str(first_schedule.enrollment.course_id)])),

            # This is used by the bulk email optout policy
            'course_ids': course_id_strs,
        })
        yield (user, first_schedule.enrollment.course.language, template_context)
