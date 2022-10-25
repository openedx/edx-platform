"""
Tests for schedules tasks
"""


import datetime
from unittest import skipUnless
from unittest.mock import DEFAULT, Mock, patch

import ddt
from django.conf import settings

from openedx.core.djangoapps.schedules.resolvers import DEFAULT_NUM_BINS
from openedx.core.djangoapps.schedules.tasks import BinnedScheduleMessageBaseTask
from openedx.core.djangoapps.schedules.tests.factories import ScheduleConfigFactory
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms


@ddt.ddt
@skip_unless_lms
@skipUnless('openedx.core.djangoapps.schedules.apps.SchedulesConfig' in settings.INSTALLED_APPS,
            "Can't test schedules if the app isn't installed")
class TestBinnedScheduleMessageBaseTask(CacheIsolationTestCase):  # lint-amnesty, pylint: disable=missing-class-docstring
    def setUp(self):
        super().setUp()

        self.site = SiteFactory.create()
        self.schedule_config = ScheduleConfigFactory.create(site=self.site)
        self.basetask = BinnedScheduleMessageBaseTask

    def test_send_enqueue_disabled(self):
        send = Mock(name='async_send_task')
        with patch.multiple(
            self.basetask,
            is_enqueue_enabled=Mock(return_value=False),
            log_info=DEFAULT,
            run=send,
        ) as patches:
            self.basetask.enqueue(
                site=self.site,
                current_date=datetime.datetime.now(),
                day_offset=2
            )
            patches['log_info'].assert_called_once_with(
                'Message queuing disabled for site %s', self.site.domain)
            send.apply_async.assert_not_called()

    @ddt.data(0, 2, -3)
    def test_send_enqueue_enabled(self, day_offset):
        send = Mock(name='async_send_task')
        current_date = datetime.datetime.now()
        with patch.multiple(
            self.basetask,
            is_enqueue_enabled=Mock(return_value=True),
            log_info=DEFAULT,
            run=send,
        ) as patches:
            self.basetask.enqueue(
                site=self.site,
                current_date=current_date,
                day_offset=day_offset
            )
            target_date = current_date.replace(hour=0, minute=0, second=0, microsecond=0) + \
                datetime.timedelta(day_offset)
            patches['log_info'].assert_any_call(
                'Target date = %s', target_date.isoformat())
            assert send.call_count == DEFAULT_NUM_BINS

    @ddt.data(True, False)
    def test_is_enqueue_enabled(self, enabled):
        with patch.object(self.basetask, 'enqueue_config_var', 'enqueue_recurring_nudge'):
            self.schedule_config.enqueue_recurring_nudge = enabled
            self.schedule_config.save()
            assert self.basetask.is_enqueue_enabled(self.site) == enabled
