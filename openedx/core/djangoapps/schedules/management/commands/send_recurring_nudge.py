from openedx.core.djangoapps.schedules.management.commands import SendEmailBaseCommand
from openedx.core.djangoapps.schedules.resolvers import ScheduleStartResolver


class Command(SendEmailBaseCommand):
    resolver_class = ScheduleStartResolver

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.log_prefix = 'Scheduled Nudge'

    def send_emails(self, resolver, *args, **options):
        for day_offset in (-3, -10):
            resolver.send(day_offset, options.get('override_recipient_email'))
