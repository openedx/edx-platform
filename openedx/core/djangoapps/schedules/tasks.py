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

from openedx.core.djangoapps.monitoring_utils import set_custom_metric

from openedx.core.djangoapps.schedules.models import Schedule, ScheduleConfig
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
    return resolvers.recurring_nudge_schedule_bin(
        _recurring_nudge_schedule_send,
        site_id,
        target_day_str,
        day_offset,
        bin_num,
        org_list,
        exclude_orgs=exclude_orgs,
        override_recipient_email=override_recipient_email,
    )


@task(ignore_result=True, routing_key=ROUTING_KEY)
def upgrade_reminder_schedule_bin(
    site_id, target_day_str, day_offset, bin_num, org_list, exclude_orgs=False, override_recipient_email=None,
):
    return resolvers.upgrade_reminder_schedule_bin(
        _upgrade_reminder_schedule_send,
        site_id,
        target_day_str,
        day_offset,
        bin_num,
        org_list,
        exclude_orgs=exclude_orgs,
        override_recipient_email=override_recipient_email,
    )

@task(ignore_result=True, routing_key=ROUTING_KEY)
def _upgrade_reminder_schedule_send(site_id, msg_str):
    site = Site.objects.get(pk=site_id)
    if not ScheduleConfig.current(site).deliver_upgrade_reminder:
        return

    msg = Message.from_string(msg_str)
    ace.send(msg)


@task(ignore_result=True, routing_key=ROUTING_KEY)
def course_update_schedule_bin(
    site_id, target_day_str, day_offset, bin_num, org_list, exclude_orgs=False, override_recipient_email=None,
):
    return resolvers.course_update_schedule_bin(
        _course_update_schedule_send,
        site_id,
        target_day_str,
        day_offset,
        bin_num,
        org_list,
        exclude_orgs=exclude_orgs,
        override_recipient_email=override_recipient_email,
    )


@task(ignore_result=True, routing_key=ROUTING_KEY)
def _course_update_schedule_send(site_id, msg_str):
    site = Site.objects.get(pk=site_id)
    if not ScheduleConfig.current(site).deliver_course_update:
        return

    msg = Message.from_string(msg_str)
    ace.send(msg)
