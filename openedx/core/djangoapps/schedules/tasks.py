import datetime
import logging

from celery.task import task, Task
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError

from django.db.utils import DatabaseError

from edx_ace import ace
from edx_ace.message import Message
from edx_ace.utils.date import deserialize, serialize
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.monitoring_utils import set_custom_metric
from openedx.core.djangoapps.schedules import message_types
from openedx.core.djangoapps.schedules.models import Schedule, ScheduleConfig
from openedx.core.djangoapps.schedules import resolvers
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration


LOG = logging.getLogger(__name__)


ROUTING_KEY = getattr(settings, 'ACE_ROUTING_KEY', None)
KNOWN_RETRY_ERRORS = (  # Errors we expect occasionally that could resolve on retry
    DatabaseError,
    ValidationError,
)


RECURRING_NUDGE_LOG_PREFIX = 'Recurring Nudge'
UPGRADE_REMINDER_LOG_PREFIX = 'Upgrade Reminder'
COURSE_UPDATE_LOG_PREFIX = 'Course Update'


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


class ScheduleMessageBaseTask(Task):
    ignore_result = True
    routing_key = ROUTING_KEY
    num_bins = resolvers.DEFAULT_NUM_BINS
    enqueue_config_var = None  # define in subclass
    log_prefix = None
    resolver = None  # define in subclass
    async_send_task = None  # define in subclass

    @classmethod
    def log_debug(cls, message, *args, **kwargs):
        LOG.debug(cls.log_prefix + ': ' + message, *args, **kwargs)

    @classmethod
    def enqueue(cls, site, current_date, day_offset, override_recipient_email=None):
        current_date = resolvers._get_datetime_beginning_of_day(current_date)

        if not cls.is_enqueue_enabled(site):
            cls.log_debug('Message queuing disabled for site %s', site.domain)
            return

        exclude_orgs, org_list = cls.get_course_org_filter(site)

        target_date = current_date + datetime.timedelta(days=day_offset)
        cls.log_debug('Target date = %s', target_date.isoformat())
        for bin in range(cls.num_bins):
            task_args = (
                site.id,
                serialize(target_date),
                day_offset,
                bin,
                org_list,
                exclude_orgs,
                override_recipient_email,
            )
            cls.log_debug('Launching task with args = %r', task_args)
            cls.apply_async(
                task_args,
                retry=False,
            )

    @classmethod
    def is_enqueue_enabled(cls, site):
        if cls.enqueue_config_var:
            return getattr(ScheduleConfig.current(site), cls.enqueue_config_var)
        return False

    @classmethod
    def get_course_org_filter(cls, site):
        """
        Given the configuration of sites, get the list of orgs that should be included or excluded from this send.

        Returns:
             tuple: Returns a tuple (exclude_orgs, org_list). If exclude_orgs is True, then org_list is a list of the
                only orgs that should be included in this send. If exclude_orgs is False, then org_list is a list of
                orgs that should be excluded from this send. All other orgs should be included.
        """
        try:
            site_config = SiteConfiguration.objects.get(site_id=site.id)
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

        return exclude_orgs, org_list

    def run(
        self, site_id, target_day_str, day_offset, bin_num, org_list, exclude_orgs=False, override_recipient_email=None,
    ):
        msg_type = self.make_message_type(day_offset)
        site = Site.objects.get(id=site_id)
        _annotate_for_monitoring(msg_type, site, bin_num, target_day_str, day_offset)
        return self.resolver(
            self.async_send_task,
            site,
            deserialize(target_day_str),
            day_offset,
            bin_num,
            org_list,
            exclude_orgs=exclude_orgs,
            override_recipient_email=override_recipient_email,
        ).send(msg_type)

    def make_message_type(self, day_offset):
        raise NotImplementedError


@task(ignore_result=True, routing_key=ROUTING_KEY)
def _recurring_nudge_schedule_send(site_id, msg_str):
    _schedule_send(
        msg_str,
        site_id,
        'deliver_recurring_nudge',
        RECURRING_NUDGE_LOG_PREFIX,
    )


@task(ignore_result=True, routing_key=ROUTING_KEY)
def _upgrade_reminder_schedule_send(site_id, msg_str):
    _schedule_send(
        msg_str,
        site_id,
        'deliver_upgrade_reminder',
        UPGRADE_REMINDER_LOG_PREFIX,
    )


@task(ignore_result=True, routing_key=ROUTING_KEY)
def _course_update_schedule_send(site_id, msg_str):
    _schedule_send(
        msg_str,
        site_id,
        'deliver_course_update',
        COURSE_UPDATE_LOG_PREFIX,
    )


class ScheduleRecurringNudge(ScheduleMessageBaseTask):
    num_bins = resolvers.RECURRING_NUDGE_NUM_BINS
    enqueue_config_var = 'enqueue_recurring_nudge'
    log_prefix = RECURRING_NUDGE_LOG_PREFIX
    resolver = resolvers.ScheduleStartResolver
    async_send_task = _recurring_nudge_schedule_send

    def make_message_type(self, day_offset):
        return message_types.RecurringNudge(abs(day_offset))


class ScheduleUpgradeReminder(ScheduleMessageBaseTask):
    num_bins = resolvers.UPGRADE_REMINDER_NUM_BINS
    enqueue_config_var = 'enqueue_upgrade_reminder'
    log_prefix = UPGRADE_REMINDER_LOG_PREFIX
    resolver = resolvers.UpgradeReminderResolver
    async_send_task = _upgrade_reminder_schedule_send

    def make_message_type(self, day_offset):
        return message_types.UpgradeReminder()


class ScheduleCourseUpdate(ScheduleMessageBaseTask):
    num_bins = resolvers.COURSE_UPDATE_NUM_BINS
    enqueue_config_var = 'enqueue_course_update'
    log_prefix = COURSE_UPDATE_LOG_PREFIX
    resolver = resolvers.CourseUpdateResolver
    async_send_task = _course_update_schedule_send

    def make_message_type(self, day_offset):
        return message_types.CourseUpdate()


def _schedule_send(msg_str, site_id, delivery_config_var, log_prefix):
    if _is_delivery_enabled(site_id, delivery_config_var, log_prefix):
        msg = Message.from_string(msg_str)
        _annonate_send_task_for_monitoring(msg)
        LOG.debug('%s: Sending message = %s', log_prefix, msg_str)
        ace.send(msg)


def _is_delivery_enabled(site_id, delivery_config_var, log_prefix):
    site = Site.objects.get(pk=site_id)
    if getattr(ScheduleConfig.current(site), delivery_config_var, False):
        return True
    else:
        LOG.debug('%s: Message delivery disabled for site %s', log_prefix, site.domain)


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


def _annonate_send_task_for_monitoring(msg):
    # A unique identifier for this batch of messages being sent.
    set_custom_metric('send_uuid', msg.send_uuid)
    # A unique identifier for this particular message.
    set_custom_metric('uuid', msg.uuid)
