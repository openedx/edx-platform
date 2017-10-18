import datetime
import logging

from celery.task import task, Task
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
from edx_ace.utils.date import deserialize, serialize
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.monitoring_utils import set_custom_metric

from openedx.core.djangoapps.schedules.models import Schedule, ScheduleConfig
from openedx.core.djangoapps.schedules import resolvers
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration


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


class ScheduleMessageBaseTask(Task):
    ignore_result = True
    routing_key = ROUTING_KEY
    num_bins = resolvers.DEFAULT_NUM_BINS
    enqueue_config_var = None  # define in subclass
    log_prefix = None

    @classmethod
    def log_debug(cls, message, *args, **kwargs):
        LOG.debug(cls.log_prefix + ': ' + message, *args, **kwargs)

    @classmethod
    def enqueue(cls, site, current_date, day_offset, override_recipient_email=None):
        current_date = current_date.replace(hour=0, minute=0, second=0)

        if not cls.is_enqueue_enabled(site):
            cls.log_debug(
                'Message queuing disabled for site %s', site.domain)
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
        finally:
            return exclude_orgs, org_list

class ScheduleRecurringNudge(ScheduleMessageBaseTask):
    num_bins = resolvers.RECURRING_NUDGE_NUM_BINS
    enqueue_config_var = 'enqueue_recurring_nudge'
    log_prefix = 'Scheduled Nudge'

    def run(
        self, site_id, target_day_str, day_offset, bin_num, org_list, exclude_orgs=False, override_recipient_email=None,
    ):
        return resolvers.ScheduleStartResolver().recurring_nudge_schedule_bin(
            _recurring_nudge_schedule_send,
            site_id,
            target_day_str,
            day_offset,
            bin_num,
            org_list,
            exclude_orgs=exclude_orgs,
            override_recipient_email=override_recipient_email,
        )


class ScheduleUpgradeReminder(ScheduleMessageBaseTask):
    num_bins = resolvers.UPGRADE_REMINDER_NUM_BINS
    enqueue_config_var = 'enqueue_upgrade_reminder'
    log_prefix = 'Course Update'


    def run(
        self, site_id, target_day_str, day_offset, bin_num, org_list, exclude_orgs=False, override_recipient_email=None,
    ):
        return resolvers.UpgradeReminderResolver().upgrade_reminder_schedule_bin(
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


class ScheduleCourseUpdate(ScheduleMessageBaseTask):
    num_bins = resolvers.COURSE_UPDATE_NUM_BINS
    enqueue_config_var = 'enqueue_course_update'
    log_prefix = 'Course Update'

    def run(
        self, site_id, target_day_str, day_offset, bin_num, org_list, exclude_orgs=False, override_recipient_email=None,
    ):
        return resolvers.CourseUpdateResolver().course_update_schedule_bin(
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
