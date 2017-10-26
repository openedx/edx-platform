import datetime
import logging
from unittest import skipUnless

import ddt
import pytz
from django.conf import settings
from edx_ace import Message
from edx_ace.utils.date import serialize
from mock import Mock, patch
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import CourseLocator

from course_modes.models import CourseMode
from course_modes.tests.factories import CourseModeFactory
from openedx.core.djangoapps.schedules import resolvers, tasks
from openedx.core.djangoapps.schedules.management.commands import send_upgrade_reminder as reminder
from openedx.core.djangoapps.schedules.management.commands.tests.tools import ScheduleBaseEmailTestBase
from openedx.core.djangoapps.schedules.tests.factories import ScheduleConfigFactory, ScheduleFactory
from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory
from openedx.core.djangoapps.waffle_utils.testutils import WAFFLE_TABLES
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

    def setUp(self):
        super(TestUpgradeReminder, self).setUp()

        CourseModeFactory(
            course_id=self.course.id,
            mode_slug=CourseMode.VERIFIED,
            expiration_datetime=datetime.datetime.now(pytz.UTC) + datetime.timedelta(days=30),
        )

    @patch.object(tasks, '_upgrade_reminder_schedule_send')
    def test_dont_send_to_verified_learner(self, mock_schedule_send):
        upgrade_deadline = datetime.datetime.now(pytz.UTC) + datetime.timedelta(days=2)
        ScheduleFactory.create(
            upgrade_deadline=upgrade_deadline,
            enrollment__user=UserFactory.create(id=resolvers.UPGRADE_REMINDER_NUM_BINS),
            enrollment__course=self.course_overview,
            enrollment__mode=CourseMode.VERIFIED,
        )
        test_datetime_str = serialize(datetime.datetime.now(pytz.UTC))

        self.tested_task.delay(
            self.site_config.site.id, target_day_str=test_datetime_str, day_offset=2, bin_num=0,
            org_list=[self.course.org],
        )

        self.assertFalse(mock_schedule_send.called)
        self.assertFalse(mock_schedule_send.apply_async.called)

    def test_filter_out_verified_schedules(self):
        now = datetime.datetime.now(pytz.UTC)
        future_datetime = now + datetime.timedelta(days=21)

        user = UserFactory.create()
        schedules = [
            ScheduleFactory.create(
                upgrade_deadline=future_datetime,
                enrollment__user=user,
                enrollment__course__self_paced=True,
                enrollment__course__end=future_datetime + datetime.timedelta(days=30),
                enrollment__course__id=CourseLocator('edX', 'toy', 'Course{}'.format(i)),
                enrollment__mode=CourseMode.VERIFIED if i in (0, 3) else CourseMode.AUDIT,
            )
            for i in range(5)
        ]

        for schedule in schedules:
            CourseModeFactory(
                course_id=schedule.enrollment.course.id,
                mode_slug=CourseMode.VERIFIED,
                expiration_datetime=future_datetime
            )

        test_datetime = future_datetime
        test_datetime_str = serialize(test_datetime)

        sent_messages = []
        with patch.object(self.tested_task, 'async_send_task') as mock_schedule_send:
            mock_schedule_send.apply_async = lambda args, *_a, **_kw: sent_messages.append(args[1])

            self.tested_task.apply(kwargs=dict(
                site_id=self.site_config.site.id, target_day_str=test_datetime_str, day_offset=2,
                bin_num=self._calculate_bin_for_user(user),
            ))

            messages = [Message.from_string(m) for m in sent_messages]
            self.assertEqual(len(messages), 1)
            message = messages[0]
            self.assertItemsEqual(
                message.context['course_ids'],
                [str(schedules[i].enrollment.course.id) for i in (1, 2, 4)]
            )
