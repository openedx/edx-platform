from openedx.core.djangoapps.schedules.management.commands import SendEmailBaseCommand
from openedx.core.djangoapps.schedules.tasks import ScheduleUpgradeReminder


class Command(SendEmailBaseCommand):
    async_send_task = ScheduleUpgradeReminder

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.log_prefix = 'Upgrade Reminder'

    def send_emails(self, *args, **kwargs):
        self.enqueue(2, *args, **kwargs)
