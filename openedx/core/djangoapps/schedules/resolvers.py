import datetime

from edx_ace.recipient_resolver import RecipientResolver
from edx_ace.utils.date import serialize

from openedx.core.djangoapps.schedules.models import ScheduleConfig
from openedx.core.djangoapps.schedules.tasks import (
    DEFAULT_NUM_BINS,
    RECURRING_NUDGE_NUM_BINS,
    UPGRADE_REMINDER_NUM_BINS,
    COURSE_UPDATE_NUM_BINS,
    recurring_nudge_schedule_bin,
    upgrade_reminder_schedule_bin,
    course_update_schedule_bin,
)
from openedx.core.djangoapps.schedules.utils import PrefixedDebugLoggerMixin
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration


class BinnedSchedulesBaseResolver(PrefixedDebugLoggerMixin, RecipientResolver):
    """
    Starts num_bins number of async tasks, each of which sends emails to an equal group of learners.

    Arguments:
        site -- Site object that filtered Schedules will be a part of
        current_date -- datetime that will be used (with time zeroed-out) as the current date in the queries

    Static attributes:
        async_send_task -- celery task function which this resolver will call out to
        num_bins -- the int number of bins to split the users into
        enqueue_config_var -- the string field name of the config variable on ScheduleConfig to check before enqueuing
    """
    async_send_task = None  # define in subclass
    num_bins = DEFAULT_NUM_BINS
    enqueue_config_var = None  # define in subclass

    def __init__(self, site, current_date, *args, **kwargs):
        super(BinnedSchedulesBaseResolver, self).__init__(*args, **kwargs)
        self.site = site
        self.current_date = current_date.replace(hour=0, minute=0, second=0)

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


class ScheduleStartResolver(BinnedSchedulesBaseResolver):
    """
    Send a message to all users whose schedule started at ``self.current_date`` + ``day_offset``.
    """
    async_send_task = recurring_nudge_schedule_bin
    num_bins = RECURRING_NUDGE_NUM_BINS
    enqueue_config_var = 'enqueue_recurring_nudge'

    def __init__(self, *args, **kwargs):
        super(ScheduleStartResolver, self).__init__(*args, **kwargs)
        self.log_prefix = 'Scheduled Nudge'


class UpgradeReminderResolver(BinnedSchedulesBaseResolver):
    """
    Send a message to all users whose verified upgrade deadline is at ``self.current_date`` + ``day_offset``.
    """
    async_send_task = upgrade_reminder_schedule_bin
    num_bins = UPGRADE_REMINDER_NUM_BINS
    enqueue_config_var = 'enqueue_upgrade_reminder'

    def __init__(self, *args, **kwargs):
        super(UpgradeReminderResolver, self).__init__(*args, **kwargs)
        self.log_prefix = 'Upgrade Reminder'


class CourseUpdateResolver(BinnedSchedulesBaseResolver):
    """
    Send a message to all users whose schedule started at ``self.current_date`` + ``day_offset`` and the
    course has updates.
    """
    async_send_task = course_update_schedule_bin
    num_bins = COURSE_UPDATE_NUM_BINS
    enqueue_config_var = 'enqueue_course_update'

    def __init__(self, *args, **kwargs):
        super(CourseUpdateResolver, self).__init__(*args, **kwargs)
        self.log_prefix = 'Course Update'
