import datetime
import logging

import pytz
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from edx_ace.recipient_resolver import RecipientResolver
from edx_ace.utils.date import serialize

from openedx.core.djangoapps.schedules.models import ScheduleConfig
from openedx.core.djangoapps.schedules.tasks import DEFAULT_NUM_BINS
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration


LOG = logging.getLogger(__name__)


class PrefixedDebugLoggerMixin(object):
    def __init__(self, *args, **kwargs):
        self.log_prefix = self.__class__.__name__

    def log_debug(self, message, *args, **kwargs):
        LOG.debug(self.log_prefix + ': ' + message, *args, **kwargs)


class BinnedSchedulesBaseResolver(RecipientResolver, PrefixedDebugLoggerMixin):
    """
    Starts num_bins number of async tasks, each of which sends emails to an equal group of learners.
    """
    def __init__(self, site, current_date, *args, **kwargs):
        super(BinnedSchedulesBaseResolver, self).__init__(*args, **kwargs)
        self.site = site
        self.current_date = current_date.replace(hour=0, minute=0, second=0)
        self.async_send_task = None  # define in subclasses
        self.num_bins = DEFAULT_NUM_BINS
        self.enqueue_config_var = None  # define in subclasses
        self.log_prefix = self.__class__.__name__

    def send(self, day_offset, override_recipient_email=None):
        if not self.is_enqueue_enabled():
            self.log_debug('Message queuing disabled for site %s', self.site.domain)
            return

        exclude_orgs, org_list = self.get_course_org_filter()

        target_date = self.current_date + datetime.timedelta(days=day_offset)
        self.log_debug('Target date = %s', target_date.isoformat())
        for bin in range(self.num_bins):
            task_args = (
                self.site.id, serialize(target_date), day_offset, bin, org_list, exclude_orgs, override_recipient_email,
            )
            self.log_debug('Launching task with args = %r', task_args)
            self.async_send_task.apply_async(
                task_args,
                retry=False,
            )

    def is_enqueue_enabled(self):
        if self.enqueue_config_var:
            return getattr(ScheduleConfig.current(self.site), self.enqueue_config_var)
        return False

    def get_course_org_filter(self):
        """
        Given the configuration of sites, get the list of orgs that should be included or excluded from this send.

        Returns:
             tuple: Returns a tuple (exclude_orgs, org_list). If exclude_orgs is True, then org_list is a list of the
                only orgs that should be included in this send. If exclude_orgs is False, then org_list is a list of
                orgs that should be excluded from this send. All other orgs should be included.
        """
        try:
            site_config = SiteConfiguration.objects.get(site_id=self.site.id)
            org_list = site_config.get_value('course_org_filter')
            exclude_orgs = False
            if not org_list:
                not_orgs = set()
                for other_site_config in SiteConfiguration.objects.all():
                    other = other_site_config.get_value('course_org_filter')
                    if not isinstance(other, list):
                        if other is not None:
                            not_orgs.add(other)
                    else:
                        not_orgs.update(other)
                org_list = list(not_orgs)
                exclude_orgs = True
            elif not isinstance(org_list, list):
                org_list = [org_list]
        except SiteConfiguration.DoesNotExist:
            org_list = None
            exclude_orgs = False
        finally:
            return exclude_orgs, org_list


class SendEmailBaseCommand(BaseCommand, PrefixedDebugLoggerMixin):
    def __init__(self, *args, **kwargs):
        super(SendEmailBaseCommand, self).__init__(*args, **kwargs)
        self.resolver_class = BinnedSchedulesBaseResolver
        self.log_prefix = self.__class__.__name__

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
        resolver = self.make_resolver(*args, **options)
        self.send_emails(resolver, *args, **options)

    def make_resolver(self, *args, **options):
        current_date = datetime.datetime(
            *[int(x) for x in options['date'].split('-')],
            tzinfo=pytz.UTC
        )
        self.log_debug('Args = %r', options)
        self.log_debug('Current date = %s', current_date.isoformat())

        site = Site.objects.get(domain__iexact=options['site_domain_name'])
        self.log_debug('Running for site %s', site.domain)
        return self.resolver_class(site, current_date)

    def send_emails(self, resolver, *args, **options):
        resolver.send(0, options.get('override_recipient_email'))
