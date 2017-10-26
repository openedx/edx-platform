import datetime
import itertools
from unittest import skipUnless

import ddt
import pytz
from django.conf import settings
from edx_ace.utils.date import serialize
from edx_ace.message import Message
from mock import Mock, patch
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import CourseLocator

from course_modes.models import CourseMode
from course_modes.tests.factories import CourseModeFactory
from courseware.models import DynamicUpgradeDeadlineConfiguration
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.core.djangoapps.schedules import resolvers, tasks
from openedx.core.djangoapps.schedules.management.commands import send_recurring_nudge as nudge
from openedx.core.djangoapps.schedules.management.commands.tests.tools import ScheduleBaseEmailTestBase
from openedx.core.djangoapps.schedules.tests.factories import ScheduleConfigFactory, ScheduleFactory
from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory
from openedx.core.djangoapps.waffle_utils.testutils import WAFFLE_TABLES
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms, FilteredQueryCountMixin
from student.tests.factories import UserFactory


# 1) Load the current django site
# 2) Query the schedules to find all of the template context information
NUM_QUERIES_NO_MATCHING_SCHEDULES = 2

# 3) Query all course modes for all courses in returned schedules
NUM_QUERIES_WITH_MATCHES = NUM_QUERIES_NO_MATCHING_SCHEDULES + 1

# 4) Load the non-matching site configurations
NUM_QUERIES_NO_ORG_LIST = 1

NUM_COURSE_MODES_QUERIES = 1


@ddt.ddt
@skip_unless_lms
@skipUnless('openedx.core.djangoapps.schedules.apps.SchedulesConfig' in settings.INSTALLED_APPS,
            "Can't test schedules if the app isn't installed")
class TestSendRecurringNudge(ScheduleBaseEmailTestBase):
    __test__ = True

    # pylint: disable=protected-access
    tested_task = tasks.ScheduleRecurringNudge
    deliver_task = tasks._recurring_nudge_schedule_send
    tested_command = nudge.Command
    deliver_config = 'deliver_recurring_nudge'
    enqueue_config = 'enqueue_recurring_nudge'
    expected_offsets = (-3, -10)

    def test_user_in_course_with_verified_coursemode_receives_upsell(self):
        user = UserFactory.create()
        course_id = CourseLocator('edX', 'toy', 'Course1')

        first_day_of_schedule = datetime.datetime.now(pytz.UTC)
        verification_deadline = first_day_of_schedule + datetime.timedelta(days=21)
        target_day = first_day_of_schedule
        target_hour_as_string = serialize(target_day)
        nudge_day = 3

        schedule = ScheduleFactory.create(start=first_day_of_schedule,
                                          enrollment__user=user,
                                          enrollment__course__id=course_id)
        schedule.enrollment.course.self_paced = True
        schedule.enrollment.course.save()

        CourseModeFactory(
            course_id=course_id,
            mode_slug=CourseMode.VERIFIED,
            expiration_datetime=verification_deadline
        )
        schedule.upgrade_deadline = verification_deadline

        bin_task_parameters = [
            target_hour_as_string,
            nudge_day,
            user,
            schedule.enrollment.course.org
        ]
        sent_messages = self._stub_sender_and_collect_sent_messages(bin_task=self.tested_task,
                                                                    stubbed_send_task=patch.object(self.tested_task, 'async_send_task'),
                                                                    bin_task_params=bin_task_parameters)

        self.assertEqual(len(sent_messages), 1)

        message_attributes = sent_messages[0][1]
        self.assertTrue(self._contains_upsell_attribute(message_attributes))

    def test_no_upsell_button_when_DUDConfiguration_is_off(self):
        DynamicUpgradeDeadlineConfiguration.objects.create(enabled=False)

        user = UserFactory.create()
        course_id = CourseLocator('edX', 'toy', 'Course1')

        first_day_of_schedule = datetime.datetime.now(pytz.UTC)
        target_day = first_day_of_schedule
        target_hour_as_string = serialize(target_day)
        nudge_day = 3

        schedule = ScheduleFactory.create(start=first_day_of_schedule,
                                          enrollment__user=user,
                                          enrollment__course__id=course_id)
        schedule.enrollment.course.self_paced = True
        schedule.enrollment.course.save()

        bin_task_parameters = [
            target_hour_as_string,
            nudge_day,
            user,
            schedule.enrollment.course.org
        ]
        sent_messages = self._stub_sender_and_collect_sent_messages(bin_task=self.tested_task,
                                                                    stubbed_send_task=patch.object(self.tested_task, 'async_send_task'),
                                                                    bin_task_params=bin_task_parameters)

        self.assertEqual(len(sent_messages), 1)

        message_attributes = sent_messages[0][1]
        self.assertFalse(self._contains_upsell_attribute(message_attributes))

    def test_user_with_no_upgrade_deadline_is_not_upsold(self):
        user = UserFactory.create()
        course_id = CourseLocator('edX', 'toy', 'Course1')

        first_day_of_schedule = datetime.datetime.now(pytz.UTC)
        target_day = first_day_of_schedule
        target_hour_as_string = serialize(target_day)
        nudge_day = 3

        schedule = ScheduleFactory.create(start=first_day_of_schedule,
                                          upgrade_deadline=None,
                                          enrollment__user=user,
                                          enrollment__course__id=course_id)
        schedule.enrollment.course.self_paced = True
        schedule.enrollment.course.save()

        verification_deadline = first_day_of_schedule + datetime.timedelta(days=21)
        CourseModeFactory(
            course_id=course_id,
            mode_slug=CourseMode.VERIFIED,
            expiration_datetime=verification_deadline
        )
        schedule.upgrade_deadline = verification_deadline

        bin_task_parameters = [
            target_hour_as_string,
            nudge_day,
            user,
            schedule.enrollment.course.org
        ]
        sent_messages = self._stub_sender_and_collect_sent_messages(bin_task=self.tested_task,
                                                                    stubbed_send_task=patch.object(self.tested_task, 'async_send_task'),
                                                                    bin_task_params=bin_task_parameters)

        self.assertEqual(len(sent_messages), 1)

        message_attributes = sent_messages[0][1]
        self.assertFalse(self._contains_upsell_attribute(message_attributes))

    def _stub_sender_and_collect_sent_messages(self, bin_task, stubbed_send_task, bin_task_params):
        sent_messages = []

        with self.settings(TEMPLATES=self._get_template_overrides()), stubbed_send_task as mock_schedule_send:

            mock_schedule_send.apply_async = lambda args, *_a, **_kw: sent_messages.append(args)

            bin_task.apply(kwargs=dict(
                site_id=self.site_config.site.id,
                target_day_str=bin_task_params[0],
                day_offset=bin_task_params[1],
                bin_num=self._calculate_bin_for_user(bin_task_params[2]),
            ))

        return sent_messages

    def _contains_upsell_attribute(self, msg_attr):
        msg = Message.from_string(msg_attr)
        tmp = msg.context["show_upsell"]
        return msg.context["show_upsell"]
