from __future__ import print_function

import logging

from openedx.core.djangoapps.schedules.management.commands import SendEmailBaseCommand, BinnedSchedulesBaseResolver
from openedx.core.djangoapps.schedules.tasks import RECURRING_NUDGE_NUM_BINS, recurring_nudge_schedule_bin

LOG = logging.getLogger(__name__)


class ScheduleStartResolver(BinnedSchedulesBaseResolver):
    """
    Send a message to all users whose schedule started at ``self.current_date`` + ``day_offset``.
    """
    def __init__(self, *args, **kwargs):
        super(ScheduleStartResolver, self).__init__(*args, **kwargs)
        self.async_send_task = recurring_nudge_schedule_bin
        self.num_bins = RECURRING_NUDGE_NUM_BINS
        self.log_prefix = 'Scheduled Nudge'
        self.enqueue_config_var = 'enqueue_recurring_nudge'


class Command(SendEmailBaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.resolver_class = ScheduleStartResolver
        self.log_prefix = 'Scheduled Nudge'

    def send_emails(self, resolver, *args, **options):
        for day_offset in (-3, -10):
            resolver.send(day_offset, options.get('override_recipient_email'))
