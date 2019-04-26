"""
Management command to send Schedule course updates
"""
from __future__ import absolute_import

from six.moves import range

from openedx.core.djangoapps.schedules.management.commands import SendEmailBaseCommand
from openedx.core.djangoapps.schedules.tasks import ScheduleCourseUpdate


class Command(SendEmailBaseCommand):
    async_send_task = ScheduleCourseUpdate
    log_prefix = 'Course Update'
    offsets = range(-7, -77, -7)
