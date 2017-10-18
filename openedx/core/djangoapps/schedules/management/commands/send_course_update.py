from openedx.core.djangoapps.schedules.management.commands import SendEmailBaseCommand
from openedx.core.djangoapps.schedules.resolvers import CourseUpdateResolver
from openedx.core.djangoapps.schedules.tasks import course_update_schedule_bin


class Command(SendEmailBaseCommand):
    resolver_class = CourseUpdateResolver
    async_send_task = course_update_schedule_bin

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.log_prefix = 'Upgrade Reminder'

    def send_emails(self, resolver, *args, **options):
        for day_offset in xrange(-7, -77, -7):
            resolver.send(day_offset, options.get('override_recipient_email'))
