"""
./manage.py lms send_access_expiry_reminder <domain>

Send out reminder emails for any students who will lose access to course content in 7 days.
"""

from openedx.core.djangoapps.schedules.management.commands import SendEmailBaseCommand
from openedx.features.course_duration_limits.tasks import CourseDurationLimitExpiryReminder
from ... import resolvers


class Command(SendEmailBaseCommand):
    async_send_task = CourseDurationLimitExpiryReminder
    log_prefix = resolvers.EXPIRY_REMINDER_LOG_PREFIX
    offsets = (7,)  # Days until Course Duration Limit expiry
