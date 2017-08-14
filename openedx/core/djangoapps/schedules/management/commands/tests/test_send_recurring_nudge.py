import datetime
from mock import patch
from unittest import TestCase

from openedx.core.djangoapps.schedules.management.commands import send_recurring_nudge as nudge


class TestSendRecurringNudge(TestCase):

    @patch.object(nudge, 'ScheduleStartResolver')
    def test_handle(self, mock_resolver):
        test_date = datetime.date(2017, 8, 1)
        nudge.Command().handle(date=test_date.isoformat())
        mock_resolver.assert_called_with(test_date)

        for week in (1, 2, 3, 4):
            mock_resolver().send.assert_any_call(week)