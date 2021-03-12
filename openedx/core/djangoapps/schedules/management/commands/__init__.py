"""
Base management command for sending emails
"""


import datetime

import pytz
from six.moves import range
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand

from openedx.core.djangoapps.schedules.utils import PrefixedDebugLoggerMixin


class SendEmailBaseCommand(PrefixedDebugLoggerMixin, BaseCommand):
    async_send_task = None  # define in subclass

    # An iterable of day offsets (e.g. -7, -14, -21, -28, ...) that defines the days for
    # which emails are sent out, relative to the 'date' parameter
    offsets = range(-7, -77, -7)

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            default=datetime.datetime.utcnow().date().isoformat(),
            help='The date to compute weekly messages relative to, in YYYY-MM-DD format',
        )
        parser.add_argument(
            '--override-recipient-email',
            help='Send all emails to this address instead of the actual recipient'
        )
        parser.add_argument('site_domain_name')
        parser.add_argument(
            '--weeks',
            type=int,
            help='Number of weekly emails to be sent',
        )

    def handle(self, *args, **options):
        self.log_debug('Args = %r', options)

        num_weeks = options.get('weeks')
        if num_weeks:
            num_days = (7 * num_weeks) + 1
            self.offsets = range(-7, -num_days, -7)

        current_date = datetime.datetime(
            *[int(x) for x in options['date'].split('-')],
            tzinfo=pytz.UTC
        )
        self.log_debug(u'Current date = %s', current_date.isoformat())

        site = Site.objects.get(domain__iexact=options['site_domain_name'])
        self.log_debug(u'Running for site %s', site.domain)

        override_recipient_email = options.get('override_recipient_email')
        self.send_emails(site, current_date, override_recipient_email)

    def enqueue(self, day_offset, site, current_date, override_recipient_email=None):
        self.async_send_task.enqueue(
            site,
            current_date,
            day_offset,
            override_recipient_email,
        )

    def send_emails(self, *args, **kwargs):
        for offset in self.offsets:
            self.enqueue(offset, *args, **kwargs)
