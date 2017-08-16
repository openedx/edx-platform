import datetime
from mock import patch, Mock
from unittest import skipUnless
import pytz

import ddt
from django.conf import settings

from student.tests.factories import UserFactory
from openedx.core.djangoapps.schedules.management.commands import send_recurring_nudge as nudge
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from openedx.core.djangoapps.schedules.tests.factories import ScheduleFactory


@ddt.ddt
@skipUnless('schedules' in settings.INSTALLED_APPS, "Can't test schedules if the app isn't installed")
class TestSendRecurringNudge(CacheIsolationTestCase):

    # pylint: disable=protected-access

    def setUp(self):
        ScheduleFactory.create(start=datetime.datetime(2017, 8, 1, 15, 44, 30, tzinfo=pytz.UTC))
        ScheduleFactory.create(start=datetime.datetime(2017, 8, 1, 17, 34, 30, tzinfo=pytz.UTC))
        ScheduleFactory.create(start=datetime.datetime(2017, 8, 2, 15, 34, 30, tzinfo=pytz.UTC))

    @patch.object(nudge, 'ScheduleStartResolver')
    def test_handle(self, mock_resolver):
        test_time = datetime.datetime(2017, 8, 1, tzinfo=pytz.UTC)
        nudge.Command().handle(date='2017-08-01')
        mock_resolver.assert_called_with(test_time)

        for week in (1, 2, 3, 4):
            mock_resolver().send.assert_any_call(week)

    @patch.object(nudge, 'ace')
    @patch.object(nudge, '_schedule_day')
    def test_resolver_send(self, mock_schedule_day, mock_ace):
        test_time = datetime.datetime(2017, 8, 1, tzinfo=pytz.UTC)
        nudge.ScheduleStartResolver(test_time).send(3)
        self.assertFalse(mock_schedule_day.called)
        mock_schedule_day.delay.assert_called_once_with(3, datetime.datetime(2017, 7, 11, tzinfo=pytz.UTC))
        self.assertFalse(mock_ace.send.called)

    @patch.object(nudge, 'ace')
    @patch.object(nudge, '_schedule_hour')
    def test_schedule_day(self, mock_schedule_hour, mock_ace):
        test_time = datetime.datetime(2017, 8, 1, tzinfo=pytz.UTC)
        nudge._schedule_day(3, test_time)
        self.assertFalse(mock_schedule_hour.called)
        self.assertEquals(mock_schedule_hour.delay.call_count, 24)
        mock_schedule_hour.delay.assert_any_call(3, test_time)
        mock_schedule_hour.delay.assert_any_call(3, test_time + datetime.timedelta(hours=23))
        self.assertFalse(mock_ace.send.called)

    @patch.object(nudge, 'ace')
    @patch.object(nudge, '_schedule_minute')
    def test_schedule_hour(self, mock_schedule_minute, mock_ace):
        test_time = datetime.datetime(2017, 8, 1, 15, tzinfo=pytz.UTC)
        nudge._schedule_hour(3, test_time)
        self.assertFalse(mock_schedule_minute.called)
        self.assertEquals(mock_schedule_minute.delay.call_count, 60)
        mock_schedule_minute.delay.assert_any_call(3, test_time)
        mock_schedule_minute.delay.assert_any_call(3, test_time + datetime.timedelta(minutes=59))
        self.assertFalse(mock_ace.send.called)

    @ddt.data(1, 10, 100)
    @patch.object(nudge, 'ace')
    @patch.object(nudge, '_schedule_send')
    def test_schedule_minute(self, schedule_count, mock_schedule_send, mock_ace):

        for _ in range(schedule_count):
            ScheduleFactory.create(start=datetime.datetime(2017, 8, 1, 15, 34, 30, tzinfo=pytz.UTC))

        test_time = datetime.datetime(2017, 8, 1, 15, 34, tzinfo=pytz.UTC)
        with self.assertNumQueries(1):
            nudge._schedule_minute(3, test_time)
        self.assertEqual(mock_schedule_send.delay.call_count, schedule_count)
        self.assertFalse(mock_ace.send.called)

    @patch.object(nudge, 'ace')
    def test_schedule_send(self, mock_ace):
        mock_msg = Mock()
        nudge._schedule_send(mock_msg)
        mock_ace.send.assert_called_exactly_once(mock_msg)
