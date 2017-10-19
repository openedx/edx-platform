import datetime
from unittest import skipUnless

import ddt
from django.conf import settings
from mock import patch, DEFAULT, Mock

from openedx.core.djangoapps.schedules.tasks import ScheduleMessageBaseTask
from openedx.core.djangoapps.schedules.resolvers import DEFAULT_NUM_BINS
from openedx.core.djangoapps.schedules.tests.factories import ScheduleConfigFactory
from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory, SiteFactory
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms


@ddt.ddt
@skip_unless_lms
@skipUnless('openedx.core.djangoapps.schedules.apps.SchedulesConfig' in settings.INSTALLED_APPS,
            "Can't test schedules if the app isn't installed")
class TestScheduleMessageBaseTask(CacheIsolationTestCase):
    def setUp(self):
        super(TestScheduleMessageBaseTask, self).setUp()

        self.site = SiteFactory.create()
        self.site_config = SiteConfigurationFactory.create(site=self.site)
        self.schedule_config = ScheduleConfigFactory.create(site=self.site)
        self.basetask = ScheduleMessageBaseTask

    def test_send_enqueue_disabled(self):
        send = Mock(name='async_send_task')
        with patch.multiple(
            self.basetask,
            is_enqueue_enabled=Mock(return_value=False),
            log_debug=DEFAULT,
            run=send,
        ) as patches:
            self.basetask.enqueue(
                site=self.site,
                current_date=datetime.datetime.now(),
                day_offset=2
            )
            patches['log_debug'].assert_called_once_with(
                'Message queuing disabled for site %s', self.site.domain)
            send.apply_async.assert_not_called()

    @ddt.data(0, 2, -3)
    def test_send_enqueue_enabled(self, day_offset):
        send = Mock(name='async_send_task')
        current_date = datetime.datetime.now()
        with patch.multiple(
            self.basetask,
            is_enqueue_enabled=Mock(return_value=True),
            get_course_org_filter=Mock(return_value=(False, None)),
            log_debug=DEFAULT,
            run=send,
        ) as patches:
            self.basetask.enqueue(
                site=self.site,
                current_date=current_date,
                day_offset=day_offset
            )
            target_date = current_date.replace(hour=0, minute=0, second=0, microsecond=0) + \
                datetime.timedelta(day_offset)
            print(patches['log_debug'].mock_calls)
            patches['log_debug'].assert_any_call(
                'Target date = %s', target_date.isoformat())
            assert send.call_count == DEFAULT_NUM_BINS

    @ddt.data(True, False)
    def test_is_enqueue_enabled(self, enabled):
        with patch.object(self.basetask, 'enqueue_config_var', 'enqueue_recurring_nudge'):
            self.schedule_config.enqueue_recurring_nudge = enabled
            self.schedule_config.save()
            assert self.basetask.is_enqueue_enabled(self.site) == enabled

    @ddt.unpack
    @ddt.data(
        ('course1', ['course1']),
        (['course1', 'course2'], ['course1', 'course2'])
    )
    def test_get_course_org_filter_include(self, course_org_filter, expected_org_list):
        self.site_config.values['course_org_filter'] = course_org_filter
        self.site_config.save()
        exclude_orgs, org_list = self.basetask.get_course_org_filter(self.site)
        assert not exclude_orgs
        assert org_list == expected_org_list

    @ddt.unpack
    @ddt.data(
        (None, []),
        ('course1', [u'course1']),
        (['course1', 'course2'], [u'course1', u'course2'])
    )
    def test_get_course_org_filter_exclude(self, course_org_filter, expected_org_list):
        self.other_site = SiteFactory.create()
        self.other_site_config = SiteConfigurationFactory.create(
            site=self.other_site,
            values={'course_org_filter': course_org_filter},
        )
        exclude_orgs, org_list = self.basetask.get_course_org_filter(self.site)
        assert exclude_orgs
        self.assertItemsEqual(org_list, expected_org_list)
