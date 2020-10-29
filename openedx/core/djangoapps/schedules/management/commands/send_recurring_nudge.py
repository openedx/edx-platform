"""
Management command to send recurring Schedule nudges
"""
from __future__ import absolute_import

from openedx.core.djangoapps.schedules.management.commands import SendEmailBaseCommand
from openedx.core.djangoapps.schedules.tasks import ScheduleRecurringNudge


class Command(SendEmailBaseCommand):
    async_send_task = ScheduleRecurringNudge
    log_prefix = 'Scheduled Nudge'
    offsets = (-3, -10)
