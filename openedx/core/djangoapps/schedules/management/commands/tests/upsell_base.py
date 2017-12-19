import datetime
import itertools
from collections import namedtuple

import ddt
from edx_ace.message import Message
from edx_ace.utils.date import serialize
from mock import patch

from courseware.models import DynamicUpgradeDeadlineConfiguration


@ddt.ddt
class ScheduleUpsellTestMixin(object):
    UpsellTestCase = namedtuple('UpsellTestCase', 'set_deadline, deadline_offset, expect_upsell')

    @ddt.data(
        *itertools.product(
            (True, False),  # enable DynamicUpgradeDeadlineConfiguration
            (
                UpsellTestCase(set_deadline=False, deadline_offset=None, expect_upsell=False),  # no deadline
                UpsellTestCase(set_deadline=True, deadline_offset=-7, expect_upsell=False),  # deadline expired
                UpsellTestCase(set_deadline=True, deadline_offset=7, expect_upsell=True),  # deadline in future
            )
        )
    )
    @ddt.unpack
    def test_upsell(self, enable_config, testcase):
        DynamicUpgradeDeadlineConfiguration.objects.create(enabled=enable_config)

        current_day, offset, target_day, _ = self._get_dates()
        upgrade_deadline = None
        if testcase.set_deadline:
            upgrade_deadline = current_day + datetime.timedelta(days=testcase.deadline_offset)

        schedule = self._schedule_factory(
            upgrade_deadline=upgrade_deadline
        )

        sent_messages = []
        with patch.object(self.task, 'async_send_task') as mock_schedule_send:
            mock_schedule_send.apply_async = lambda args, *_a, **_kw: sent_messages.append(args[1])
            self.task().apply(kwargs=dict(
                site_id=self.site_config.site.id, target_day_str=serialize(target_day), day_offset=offset,
                bin_num=self._calculate_bin_for_user(schedule.enrollment.user),
            ))
        self.assertEqual(len(sent_messages), 1)

        found_upsell = self._contains_upsell(sent_messages[0])
        expect_upsell = enable_config and testcase.expect_upsell
        self.assertEqual(found_upsell, expect_upsell)

    def _contains_upsell(self, message_str):
        message = Message.from_string(message_str)
        return message.context["show_upsell"]
