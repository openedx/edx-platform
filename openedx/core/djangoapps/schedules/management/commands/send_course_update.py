from openedx.core.djangoapps.schedules.management.commands import SendEmailBaseCommand
from openedx.core.djangoapps.schedules.tasks import ScheduleCourseUpdate


class Command(SendEmailBaseCommand):
    async_send_task = ScheduleCourseUpdate
    log_prefix = 'Course Update'
    offsets = xrange(-7, -77, -7)
