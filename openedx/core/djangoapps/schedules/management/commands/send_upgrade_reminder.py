"""
A management command to send Schedule upgrade reminders
"""


from textwrap import dedent

from openedx.core.djangoapps.schedules.management.commands import SendEmailBaseCommand
from openedx.core.djangoapps.schedules.tasks import ScheduleUpgradeReminder


class Command(SendEmailBaseCommand):
    """
    A management command to send Schedule upgrade reminders
    """
    help = dedent(__doc__).strip()
    async_send_task = ScheduleUpgradeReminder
    log_prefix = 'Upgrade Reminder'
    offsets = (2,)
