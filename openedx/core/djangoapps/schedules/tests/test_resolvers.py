import datetime
from unittest import skipUnless

import ddt
from django.conf import settings
from mock import patch

from openedx.core.djangoapps.schedules.resolvers import BinnedSchedulesBaseResolver
from openedx.core.djangoapps.schedules.tasks import DEFAULT_NUM_BINS
from openedx.core.djangoapps.schedules.tests.factories import ScheduleConfigFactory
from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory, SiteFactory
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms


@ddt.ddt
@skip_unless_lms
@skipUnless('openedx.core.djangoapps.schedules.apps.SchedulesConfig' in settings.INSTALLED_APPS,
            "Can't test schedules if the app isn't installed")
class TestBinnedSchedulesBaseResolver(CacheIsolationTestCase):
    def setUp(self):
        super(TestBinnedSchedulesBaseResolver, self).setUp()

        self.site = SiteFactory.create()
        self.site_config = SiteConfigurationFactory.create(site=self.site)
        self.schedule_config = ScheduleConfigFactory.create(site=self.site)

    def setup_resolver(self, site=None, current_date=None):
        if site is None:
            site = self.site
        if current_date is None:
            current_date = datetime.datetime.now()
        resolver = BinnedSchedulesBaseResolver(self.site, current_date)
        return resolver

    def test_init_site(self):
        resolver = self.setup_resolver()
        assert resolver.site == self.site

    def test_init_current_date(self):
        current_time = datetime.datetime.now()
        resolver = self.setup_resolver(current_date=current_time)
        current_date = current_time.replace(hour=0, minute=0, second=0)
        assert resolver.current_date == current_date

    def test_init_async_send_task(self):
        resolver = self.setup_resolver()
        assert resolver.async_send_task is None

    def test_init_num_bins(self):
        resolver = self.setup_resolver()
        assert resolver.num_bins == DEFAULT_NUM_BINS

    def test_send_enqueue_disabled(self):
        resolver = self.setup_resolver()
        resolver.is_enqueue_enabled = lambda: False
        with patch.object(resolver, 'async_send_task') as send:
            with patch.object(resolver, 'log_debug') as log_debug:
                resolver.send(day_offset=2)
                log_debug.assert_called_once_with('Message queuing disabled for site %s', self.site.domain)
                send.apply_async.assert_not_called()

    @ddt.data(0, 2, -3)
    def test_send_enqueue_enabled(self, day_offset):
        resolver = self.setup_resolver()
        resolver.is_enqueue_enabled = lambda: True
        resolver.get_course_org_filter = lambda: (False, None)
        with patch.object(resolver, 'async_send_task') as send:
            with patch.object(resolver, 'log_debug') as log_debug:
                resolver.send(day_offset=day_offset)
                target_date = resolver.current_date + datetime.timedelta(day_offset)
                log_debug.assert_any_call('Target date = %s', target_date.isoformat())
                assert send.apply_async.call_count == DEFAULT_NUM_BINS

    @ddt.data(True, False)
    def test_is_enqueue_enabled(self, enabled):
        resolver = self.setup_resolver()
        resolver.enqueue_config_var = 'enqueue_recurring_nudge'
        self.schedule_config.enqueue_recurring_nudge = enabled
        self.schedule_config.save()
        assert resolver.is_enqueue_enabled() == enabled

    @ddt.unpack
    @ddt.data(
        ('course1', ['course1']),
        (['course1', 'course2'], ['course1', 'course2'])
    )
    def test_get_course_org_filter_include(self, course_org_filter, expected_org_list):
        resolver = self.setup_resolver()
        self.site_config.values['course_org_filter'] = course_org_filter
        self.site_config.save()
        exclude_orgs, org_list = resolver.get_course_org_filter()
        assert not exclude_orgs
        assert org_list == expected_org_list

    @ddt.unpack
    @ddt.data(
        (None, []),
        ('course1', [u'course1']),
        (['course1', 'course2'], [u'course1', u'course2'])
    )
    def test_get_course_org_filter_exclude(self, course_org_filter, expected_org_list):
        resolver = self.setup_resolver()
        self.other_site = SiteFactory.create()
        self.other_site_config = SiteConfigurationFactory.create(
            site=self.other_site,
            values={'course_org_filter': course_org_filter},
        )
        exclude_orgs, org_list = resolver.get_course_org_filter()
        assert exclude_orgs
        self.assertItemsEqual(org_list, expected_org_list)
