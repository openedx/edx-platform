from openedx.core.djangoapps.schedules.management.commands import SendEmailBaseCommand
from openedx.core.djangoapps.schedules.tasks import ScheduleRecurringNudge


class Command(SendEmailBaseCommand):
    async_send_task = ScheduleRecurringNudge
    log_prefix = 'Scheduled Nudge'

    def send_emails(self, *args, **kwargs):
        for day_offset in (-3, -10):
            self.enqueue(day_offset, *args, **kwargs)
