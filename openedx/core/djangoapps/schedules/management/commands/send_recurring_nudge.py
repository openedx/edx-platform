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
            return

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

        target_date = self.current_date - datetime.timedelta(days=day)
        for hour in range(24):
            target_hour = target_date + datetime.timedelta(hours=hour)
            recurring_nudge_schedule_hour.apply_async(
                (self.site.id, day, serialize(target_hour), org_list, exclude_orgs, override_recipient_email),
                retry=False,
            )


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
        site = Site.objects.get(domain__iexact=options['site_domain_name'])
        resolver = ScheduleStartResolver(site, current_date)
        for day in (3, 10):
            resolver.send(day, options.get('override_recipient_email'))
