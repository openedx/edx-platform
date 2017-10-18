import datetime
import logging

from celery.task import task
from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db.utils import DatabaseError
from django.utils.formats import dateformat, get_format

from edx_ace import ace
from edx_ace.message import Message
from edx_ace.recipient import Recipient
from edx_ace.utils.date import deserialize
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.monitoring_utils import set_custom_metric, function_trace

from openedx.core.djangoapps.schedules.models import Schedule, ScheduleConfig
from openedx.core.djangoapps.schedules.message_type import ScheduleMessageType
from openedx.core.djangoapps.schedules import resolvers


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
def _recurring_nudge_schedule_send(site_id, msg_str):
    site = Site.objects.get(pk=site_id)
    if not ScheduleConfig.current(site).deliver_recurring_nudge:
        LOG.debug('Recurring Nudge: Message delivery disabled for site %s', site.domain)
        return

    msg = Message.from_string(msg_str)
    # A unique identifier for this batch of messages being sent.
    set_custom_metric('send_uuid', msg.send_uuid)
    # A unique identifier for this particular message.
    set_custom_metric('uuid', msg.uuid)
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
    site = Site.objects.get(id=site_id)

    _annotate_for_monitoring(msg_type, site, bin_num, target_day_str, day_offset)

    for (user, language, context) in resolvers._recurring_nudge_schedules_for_bin(
        site,
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
        with function_trace('enqueue_send_task'):
            _recurring_nudge_schedule_send.apply_async((site_id, str(msg)), retry=False)


def _annotate_for_monitoring(message_type, site, bin_num, target_day_str, day_offset):
    # This identifies the type of message being sent, for example: schedules.recurring_nudge3.
    set_custom_metric('message_name', '{0}.{1}'.format(message_type.app_label, message_type.name))
    # The domain name of the site we are sending the message for.
    set_custom_metric('site', site.domain)
    # This is the "bin" of data being processed. We divide up the work into chunks so that we don't tie up celery
    # workers for too long. This could help us identify particular bins that are problematic.
    set_custom_metric('bin', bin_num)
    # The date we are processing data for.
    set_custom_metric('target_day', target_day_str)
    # The number of days relative to the current date to process data for.
    set_custom_metric('day_offset', day_offset)
    # A unique identifier for this batch of messages being sent.
    set_custom_metric('send_uuid', message_type.uuid)


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
    site = Site.objects.get(id=site_id)

    _annotate_for_monitoring(msg_type, site, bin_num, target_day_str, day_offset)

    for (user, language, context) in resolvers._upgrade_reminder_schedules_for_bin(
        site,
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
        with function_trace('enqueue_send_task'):
            _upgrade_reminder_schedule_send.apply_async((site_id, str(msg)), retry=False)


@task(ignore_result=True, routing_key=ROUTING_KEY)
def _upgrade_reminder_schedule_send(site_id, msg_str):
    site = Site.objects.get(pk=site_id)
    if not ScheduleConfig.current(site).deliver_upgrade_reminder:
        return

    msg = Message.from_string(msg_str)
    ace.send(msg)


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
    site = Site.objects.get(id=site_id)

    _annotate_for_monitoring(msg_type, site, bin_num, target_day_str, day_offset)

    for (user, language, context) in resolvers._course_update_schedules_for_bin(
        site,
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
        with function_trace('enqueue_send_task'):
            _course_update_schedule_send.apply_async((site_id, str(msg)), retry=False)


@task(ignore_result=True, routing_key=ROUTING_KEY)
def _course_update_schedule_send(site_id, msg_str):
    site = Site.objects.get(pk=site_id)
    if not ScheduleConfig.current(site).deliver_course_update:
        return

    msg = Message.from_string(msg_str)
    ace.send(msg)
