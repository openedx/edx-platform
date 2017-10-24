from openedx.core.djangoapps.schedules.management.commands import SendEmailBaseCommand
from openedx.core.djangoapps.schedules.tasks import ScheduleCourseUpdate


class Command(SendEmailBaseCommand):
    async_send_task = ScheduleCourseUpdate

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.log_prefix = 'Upgrade Reminder'

    def send_emails(self, *args, **kwargs):
        for day_offset in xrange(-7, -77, -7):
            self.enqueue(day_offset, *args, **kwargs)
