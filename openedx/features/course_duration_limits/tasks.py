"""
Tasks requiring asynchronous handling for course_duration_limits
"""

from __future__ import absolute_import

import datetime
import logging

import six
import waffle
from celery import task
from celery_utils.logged_task import LoggedTask
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from edx_ace import ace
from edx_ace.message import Message
from edx_ace.utils.date import deserialize, serialize
from edx_django_utils.monitoring import set_custom_metric
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.schedules.resolvers import _get_datetime_beginning_of_day
from openedx.core.djangoapps.schedules.tasks import _annonate_send_task_for_monitoring, _track_message_sent
from openedx.core.lib.celery.task_utils import emulate_http_request

from . import message_types, resolvers
from .models import CourseDurationLimitConfig

LOG = logging.getLogger(__name__)
ROUTING_KEY = getattr(settings, 'ACE_ROUTING_KEY', None)


class CourseDurationLimitMessageBaseTask(LoggedTask):
    """
    Base class for top-level Schedule tasks that create subtasks
    for each Bin.
    """
    ignore_result = True
    routing_key = ROUTING_KEY
    num_bins = resolvers.DEFAULT_NUM_BINS
    enqueue_config_var = None  # define in subclass
    log_prefix = None
    resolver = None  # define in subclass
    async_send_task = None  # define in subclass

    @classmethod
    def log_debug(cls, message, *args, **kwargs):
        """
        Wrapper around LOG.debug that prefixes the message.
        """
        LOG.debug(cls.log_prefix + ': ' + message, *args, **kwargs)

    @classmethod
    def log_info(cls, message, *args, **kwargs):
        """
        Wrapper around LOG.info that prefixes the message.
        """
        LOG.info(cls.log_prefix + ': ' + message, *args, **kwargs)

    @classmethod
    def enqueue(cls, site, current_date, day_offset, override_recipient_email=None):
        current_date = _get_datetime_beginning_of_day(current_date)

        for course_key, config in CourseDurationLimitConfig.all_current_course_configs().items():
            if not config['enabled'][0]:
                cls.log_info(u'Course duration limits disabled for course_key %s, skipping', course_key)
                continue

            # enqueue_enabled, _ = config[cls.enqueue_config_var]
            # TODO: Switch over to a model where enqueing is based in CourseDurationLimitConfig
            enqueue_enabled = waffle.switch_is_active('course_duration_limits.enqueue_enabled')

            if not enqueue_enabled:
                cls.log_info(u'Message queuing disabled for course_key %s', course_key)
                continue

            target_date = current_date + datetime.timedelta(days=day_offset)
            task_args = (
                site.id,
                six.text_type(course_key),
                serialize(target_date),
                day_offset,
                override_recipient_email,
            )
            cls().apply_async(
                task_args,
                retry=False,
            )

    def run(  # pylint: disable=arguments-differ
        self, site_id, course_key_str, target_day_str, day_offset, override_recipient_email=None,
    ):
        try:
            site = Site.objects.select_related('configuration').get(id=site_id)
            with emulate_http_request(site=site):
                msg_type = self.make_message_type(day_offset)
                _annotate_for_monitoring(msg_type, course_key_str, target_day_str, day_offset)
                return self.resolver(  # pylint: disable=not-callable
                    self.async_send_task,
                    site,
                    CourseKey.from_string(course_key_str),
                    deserialize(target_day_str),
                    day_offset,
                    override_recipient_email=override_recipient_email,
                ).send(msg_type)
        except Exception:  # pylint: disable=broad-except
            LOG.exception("Task failed")

    def make_message_type(self, day_offset):
        raise NotImplementedError


@task(base=LoggedTask, ignore_result=True, routing_key=ROUTING_KEY)
def _expiry_reminder_schedule_send(site_id, msg_str):
    _schedule_send(
        msg_str,
        site_id,
        'deliver_expiry_reminder',
        resolvers.EXPIRY_REMINDER_LOG_PREFIX,
    )


class CourseDurationLimitExpiryReminder(CourseDurationLimitMessageBaseTask):
    """
    Task to send out a reminder that a users access to course content is expiring soon.
    """
    num_bins = resolvers.EXPIRY_REMINDER_NUM_BINS
    enqueue_config_var = 'enqueue_expiry_reminder'
    log_prefix = resolvers.EXPIRY_REMINDER_LOG_PREFIX
    resolver = resolvers.ExpiryReminderResolver
    async_send_task = _expiry_reminder_schedule_send

    def make_message_type(self, day_offset):
        return message_types.ExpiryReminder()


def _schedule_send(msg_str, site_id, delivery_config_var, log_prefix):
    site = Site.objects.select_related('configuration').get(pk=site_id)
    if _is_delivery_enabled(site, delivery_config_var, log_prefix):
        msg = Message.from_string(msg_str)

        user = User.objects.get(username=msg.recipient.username)  # pylint: disable=no-member
        with emulate_http_request(site=site, user=user):
            _annonate_send_task_for_monitoring(msg)
            LOG.debug(u'%s: Sending message = %s', log_prefix, msg_str)
            ace.send(msg)
            _track_message_sent(site, user, msg)


def _is_delivery_enabled(site, delivery_config_var, log_prefix):  # pylint: disable=unused-argument
    # Experiment TODO: when this is going to prod, switch over to a config-model backed solution
    #if getattr(CourseDurationLimitConfig.current(site=site), delivery_config_var, False):
    if waffle.switch_is_active('course_duration_limits.delivery_enabled'):
        return True
    else:
        LOG.info(u'%s: Message delivery disabled for site %s', log_prefix, site.domain)
        return False


def _annotate_for_monitoring(message_type, course_key, target_day_str, day_offset):
    """
    Set custom metrics in monitoring to make it easier to identify what messages are being sent and why.
    """
    # This identifies the type of message being sent, for example: schedules.recurring_nudge3.
    set_custom_metric('message_name', '{0}.{1}'.format(message_type.app_label, message_type.name))
    # The domain name of the site we are sending the message for.
    set_custom_metric('course_key', course_key)
    # The date we are processing data for.
    set_custom_metric('target_day', target_day_str)
    # The number of days relative to the current date to process data for.
    set_custom_metric('day_offset', day_offset)
    # A unique identifier for this batch of messages being sent.
    set_custom_metric('send_uuid', message_type.uuid)
