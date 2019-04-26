"""
A management command to send Schedule upgrade reminders
"""
from __future__ import absolute_import

from openedx.core.djangoapps.schedules.management.commands import SendEmailBaseCommand
from openedx.core.djangoapps.schedules.tasks import ScheduleUpgradeReminder


class Command(SendEmailBaseCommand):
    async_send_task = ScheduleUpgradeReminder
    log_prefix = 'Upgrade Reminder'
    offsets = (2,)
