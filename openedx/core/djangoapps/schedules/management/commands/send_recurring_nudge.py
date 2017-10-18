from openedx.core.djangoapps.schedules.management.commands import SendEmailBaseCommand
from openedx.core.djangoapps.schedules.resolvers import ScheduleStartResolver
from openedx.core.djangoapps.schedules.tasks import recurring_nudge_schedule_bin


class Command(SendEmailBaseCommand):
    resolver_class = ScheduleStartResolver
    async_send_task = recurring_nudge_schedule_bin

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.log_prefix = 'Scheduled Nudge'

    def send_emails(self, resolver, *args, **options):
        for day_offset in (-3, -10):
            resolver.send(day_offset, options.get('override_recipient_email'))
