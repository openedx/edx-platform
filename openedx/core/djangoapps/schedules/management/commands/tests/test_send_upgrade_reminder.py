import logging
from unittest import skipUnless

import ddt
from django.conf import settings
from edx_ace import Message
from edx_ace.utils.date import serialize
from mock import Mock, patch
from opaque_keys.edx.locator import CourseLocator

from course_modes.models import CourseMode
from openedx.core.djangoapps.schedules import tasks
from openedx.core.djangoapps.schedules.management.commands import send_upgrade_reminder as reminder
from openedx.core.djangoapps.schedules.management.commands.tests.tools import ScheduleBaseEmailTestBase
from openedx.core.djangoapps.schedules.tests.factories import ScheduleFactory
from openedx.core.djangolib.testing.utils import skip_unless_lms
from student.tests.factories import UserFactory


LOG = logging.getLogger(__name__)


@ddt.ddt
@skip_unless_lms
@skipUnless('openedx.core.djangoapps.schedules.apps.SchedulesConfig' in settings.INSTALLED_APPS,
            "Can't test schedules if the app isn't installed")
class TestUpgradeReminder(ScheduleBaseEmailTestBase):
    __test__ = True

    tested_task = tasks.ScheduleUpgradeReminder
    deliver_task = tasks._upgrade_reminder_schedule_send
    tested_command = reminder.Command
    deliver_config = 'deliver_upgrade_reminder'
    enqueue_config = 'enqueue_upgrade_reminder'
    expected_offsets = (2,)

    has_course_queries = True

    @ddt.data(True, False)
    @patch.object(tasks, 'ace')
    def test_verified_learner(self, is_verified, mock_ace):
        user = UserFactory.create(id=self.tested_task.num_bins)
        current_day, offset, target_day = self._get_dates()
        ScheduleFactory.create(
            upgrade_deadline=target_day,
            enrollment__course__self_paced=True,
            enrollment__user=user,
            enrollment__mode=CourseMode.VERIFIED if is_verified else CourseMode.AUDIT,
        )

        self.tested_task.apply(kwargs=dict(
            site_id=self.site_config.site.id, target_day_str=serialize(target_day), day_offset=offset,
            bin_num=self._calculate_bin_for_user(user),
        ))

        self.assertEqual(mock_ace.send.called, not is_verified)

    def test_filter_out_verified_schedules(self):
        current_day, offset, target_day = self._get_dates()

        user = UserFactory.create()
        schedules = [
            ScheduleFactory.create(
                upgrade_deadline=target_day,
                enrollment__user=user,
                enrollment__course__self_paced=True,
                enrollment__course__id=CourseLocator('edX', 'toy', 'Course{}'.format(i)),
                enrollment__mode=CourseMode.VERIFIED if i in (0, 3) else CourseMode.AUDIT,
            )
            for i in range(5)
        ]

        sent_messages = []
        with patch.object(self.tested_task, 'async_send_task') as mock_schedule_send:
            mock_schedule_send.apply_async = lambda args, *_a, **_kw: sent_messages.append(args[1])

            self.tested_task.apply(kwargs=dict(
                site_id=self.site_config.site.id, target_day_str=serialize(target_day), day_offset=offset,
                bin_num=self._calculate_bin_for_user(user),
            ))

            messages = [Message.from_string(m) for m in sent_messages]
            self.assertEqual(len(messages), 1)
            message = messages[0]
            self.assertItemsEqual(
                message.context['course_ids'],
                [str(schedules[i].enrollment.course.id) for i in (1, 2, 4)]
            )
