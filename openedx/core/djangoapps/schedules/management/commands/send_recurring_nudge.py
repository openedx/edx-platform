from __future__ import print_function

import datetime
import logging

from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
import pytz

from edx_ace.utils.date import serialize
from openedx.core.djangoapps.schedules.models import ScheduleConfig
from openedx.core.djangoapps.schedules.tasks import recurring_nudge_schedule_hour
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration

from edx_ace.recipient_resolver import RecipientResolver

LOG = logging.getLogger(__name__)


class ScheduleStartResolver(RecipientResolver):
    def __init__(self, site, current_date):
        self.site = site
        self.current_date = current_date.replace(hour=0, minute=0, second=0)

    def send(self, day, override_recipient_email=None):
        """
        Send a message to all users whose schedule started at ``self.current_date`` - ``day``.
        """
        if not ScheduleConfig.current(self.site).enqueue_recurring_nudge:
            LOG.debug('Recurring Nudge: Message queuing disabled for site %s', self.site.domain)
            return

        exclude_orgs, org_list = self.get_org_filter()

        target_date = self.current_date - datetime.timedelta(days=day)
        LOG.debug('Scheduled Nudge: Target date = %s', target_date.isoformat())
        for hour in range(24):
            target_hour = target_date + datetime.timedelta(hours=hour)
            task_args = (self.site.id, day, serialize(target_hour), org_list, exclude_orgs, override_recipient_email)
            LOG.debug('Scheduled Nudge: Launching task with args = %r', task_args)
            recurring_nudge_schedule_hour.apply_async(task_args, retry=False)

    def get_org_filter(self):
        """
        Given the configuration of sites, get the list of orgs that should be included or excluded from this send.

        Returns:
             tuple: Returns a tuple (exclude_orgs, org_list). If exclude_orgs is True, then org_list is a list of the
                only orgs that should be included in this send. If exclude_orgs is False, then org_list is a list of
                orgs that should be excluded from this send. All other orgs should be included.
        """
        try:
            site_config = SiteConfiguration.objects.get(site_id=self.site.id)
            org_list = site_config.values.get('course_org_filter', None)
            exclude_orgs = False
            if not org_list:
                not_orgs = set()
                for other_site_config in SiteConfiguration.objects.all():
                    not_orgs.update(other_site_config.values.get('course_org_filter', []))
                org_list = list(not_orgs)
                exclude_orgs = True
            elif not isinstance(org_list, list):
                org_list = [org_list]
        except SiteConfiguration.DoesNotExist:
            org_list = None
            exclude_orgs = False
        return exclude_orgs, org_list


class Command(BaseCommand):

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

    def handle(self, *args, **options):
        current_date = datetime.datetime(
            *[int(x) for x in options['date'].split('-')],
            tzinfo=pytz.UTC
        )
        LOG.debug('Scheduled Nudge: Args = %r', options)
        LOG.debug('Scheduled Nudge: Current date = %s', current_date.isoformat())

        site = Site.objects.get(domain__iexact=options['site_domain_name'])
        LOG.debug('Scheduled Nudge: Running for site %s', site.domain)
        resolver = ScheduleStartResolver(site, current_date)
        for day in (3, 10):
            resolver.send(day, options.get('override_recipient_email'))
