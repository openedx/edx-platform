"""
Management command to send recurring Schedule nudges
"""


from textwrap import dedent

from openedx.core.djangoapps.schedules.management.commands import SendEmailBaseCommand
from openedx.core.djangoapps.schedules.tasks import ScheduleRecurringNudge


class Command(SendEmailBaseCommand):
    """
    Command to send recurring Schedule nudges
    """
    help = dedent(__doc__).strip()
    async_send_task = ScheduleRecurringNudge
    log_prefix = 'Scheduled Nudge'
    offsets = (-3, -10)
