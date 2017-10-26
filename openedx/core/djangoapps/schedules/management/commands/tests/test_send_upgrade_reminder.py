import datetime
from copy import deepcopy
import logging
from unittest import skipUnless

import attr
import ddt
import pytz
from django.conf import settings
from edx_ace import Message
from edx_ace.channel import ChannelType
from edx_ace.test_utils import StubPolicy, patch_channels, patch_policies
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


SITE_QUERY = 1
SCHEDULES_QUERY = 1
COURSE_MODES_QUERY = 1
GLOBAL_DEADLINE_SWITCH_QUERY = 1
COMMERCE_CONFIG_QUERY = 1
NUM_QUERIES_NO_ORG_LIST = 1

NUM_QUERIES_NO_MATCHING_SCHEDULES = SITE_QUERY + SCHEDULES_QUERY

NUM_QUERIES_WITH_MATCHES = (
    NUM_QUERIES_NO_MATCHING_SCHEDULES +
    COURSE_MODES_QUERY
)

NUM_QUERIES_FIRST_MATCH = (
    NUM_QUERIES_WITH_MATCHES
    + GLOBAL_DEADLINE_SWITCH_QUERY
    + COMMERCE_CONFIG_QUERY
)

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
    expected_offsets = (2,)

    has_course_queries = True

    def setUp(self):
        super(TestUpgradeReminder, self).setUp()

        CourseModeFactory(
            course_id=self.course.id,
            mode_slug=CourseMode.VERIFIED,
            expiration_datetime=datetime.datetime.now(pytz.UTC) + datetime.timedelta(days=30),
        )

    @patch.object(tasks, 'ace')
    @patch.object(tested_task, 'apply_async')
    def test_enqueue_disabled(self, mock_ace, mock_apply_async):
        ScheduleConfigFactory.create(site=self.site_config.site, enqueue_upgrade_reminder=False)

        current_day = datetime.datetime(2017, 8, 1, tzinfo=pytz.UTC)
        self.tested_task.enqueue(
            self.site_config.site,
            current_day,
            day_offset=3,
        )
        self.assertFalse(mock_apply_async.called)
        self.assertFalse(mock_ace.send.called)

    @patch.object(tasks, 'ace')
    @patch.object(tested_task, 'async_send_task')
    @ddt.data(
        ((['filtered_org'], [], 1)),
        (([], ['filtered_org'], 2))
    )
    @ddt.unpack
    def test_site_config(self, this_org_list, other_org_list, expected_message_count, mock_schedule_send, mock_ace):
        filtered_org = 'filtered_org'
        unfiltered_org = 'unfiltered_org'
        this_config = SiteConfigurationFactory.create(values={'course_org_filter': this_org_list})
        other_config = SiteConfigurationFactory.create(values={'course_org_filter': other_org_list})

        for config in (this_config, other_config):
            ScheduleConfigFactory.create(site=config.site)

        user1 = UserFactory.create(id=resolvers.UPGRADE_REMINDER_NUM_BINS)
        user2 = UserFactory.create(id=resolvers.UPGRADE_REMINDER_NUM_BINS * 2)

        ScheduleFactory.create(
            upgrade_deadline=datetime.datetime(2017, 8, 3, 17, 44, 30, tzinfo=pytz.UTC),
            enrollment__course__org=filtered_org,
            enrollment__course__self_paced=True,
            enrollment__user=user1,
        )
        ScheduleFactory.create(
            upgrade_deadline=datetime.datetime(2017, 8, 3, 17, 44, 30, tzinfo=pytz.UTC),
            enrollment__course__org=unfiltered_org,
            enrollment__course__self_paced=True,
            enrollment__user=user1,
        )
        ScheduleFactory.create(
            upgrade_deadline=datetime.datetime(2017, 8, 3, 17, 44, 30, tzinfo=pytz.UTC),
            enrollment__course__org=unfiltered_org,
            enrollment__course__self_paced=True,
            enrollment__user=user2,
        )

        test_datetime = datetime.datetime(2017, 8, 3, 17, tzinfo=pytz.UTC)
        test_datetime_str = serialize(test_datetime)

        course_switch_queries = 1
        org_switch_queries = 1
        expected_queries = NUM_QUERIES_FIRST_MATCH + course_switch_queries + org_switch_queries
        if not this_org_list:
            expected_queries += NUM_QUERIES_NO_ORG_LIST

        with self.assertNumQueries(expected_queries, table_blacklist=WAFFLE_TABLES):
            self.tested_task.apply(kwargs=dict(
                site_id=this_config.site.id, target_day_str=test_datetime_str, day_offset=-3, bin_num=0
            ))

        self.assertEqual(mock_schedule_send.apply_async.call_count, expected_message_count)
        self.assertFalse(mock_ace.send.called)

    @patch.object(tasks, 'ace')
    @patch.object(tested_task, 'async_send_task')
    def test_multiple_enrollments(self, mock_schedule_send, mock_ace):
        user = UserFactory.create()
        schedules = [
            ScheduleFactory.create(
                upgrade_deadline=datetime.datetime(2017, 8, 3, 19, 44, 30, tzinfo=pytz.UTC),
                enrollment__user=user,
                enrollment__course__self_paced=True,
                enrollment__course__id=CourseLocator('edX', 'toy', 'Course{}'.format(course_num))
            )
            for course_num in (1, 2, 3)
        ]

        course_switch_queries = len(set(s.enrollment.course.id for s in schedules))
        org_switch_queries = len(set(s.enrollment.course.id.org for s in schedules))

        test_datetime = datetime.datetime(2017, 8, 3, 19, 44, 30, tzinfo=pytz.UTC)
        test_datetime_str = serialize(test_datetime)
        expected_query_count = (
            NUM_QUERIES_FIRST_MATCH + course_switch_queries + org_switch_queries + NUM_QUERIES_NO_ORG_LIST
        )
        with self.assertNumQueries(expected_query_count, table_blacklist=WAFFLE_TABLES):
            self.tested_task.apply(kwargs=dict(
                site_id=self.site_config.site.id, target_day_str=test_datetime_str, day_offset=2,
                bin_num=self._calculate_bin_for_user(user),
            ))
        self.assertEqual(mock_schedule_send.apply_async.call_count, 1)
        self.assertFalse(mock_ace.send.called)

    @ddt.data(1, 10, 100)
    def test_templates(self, message_count):
        now = datetime.datetime.now(pytz.UTC)
        future_datetime = now + datetime.timedelta(days=21)

        user = UserFactory.create()
        schedules = [
            ScheduleFactory.create(
                upgrade_deadline=future_datetime,
                enrollment__user=user,
                enrollment__course__self_paced=True,
                enrollment__course__end=future_datetime + datetime.timedelta(days=30),
                enrollment__course__id=CourseLocator('edX', 'toy', 'Course{}'.format(course_num))
            )
            for course_num in range(message_count)
        ]

        for schedule in schedules:
            CourseModeFactory(
                course_id=schedule.enrollment.course.id,
                mode_slug=CourseMode.VERIFIED,
                expiration_datetime=future_datetime
            )

        course_switch_queries = len(set(s.enrollment.course.id for s in schedules))
        org_switch_queries = len(set(s.enrollment.course.id.org for s in schedules))

        test_datetime = future_datetime
        test_datetime_str = serialize(test_datetime)

        patch_policies(self, [StubPolicy([ChannelType.PUSH])])
        mock_channel = Mock(
            name='test_channel',
            channel_type=ChannelType.EMAIL
        )
        patch_channels(self, [mock_channel])

        sent_messages = []

        with self.settings(TEMPLATES=self._get_template_overrides()):
            with patch.object(self.tested_task, 'async_send_task') as mock_schedule_send:
                mock_schedule_send.apply_async = lambda args, *_a, **_kw: sent_messages.append(args)

                # we execute one query per course to see if it's opted out of dynamic upgrade deadlines
                num_expected_queries = (
                    NUM_QUERIES_FIRST_MATCH + NUM_QUERIES_NO_ORG_LIST + course_switch_queries + org_switch_queries
                )

                with self.assertNumQueries(num_expected_queries, table_blacklist=WAFFLE_TABLES):
                    self.tested_task.apply(kwargs=dict(
                        site_id=self.site_config.site.id, target_day_str=test_datetime_str, day_offset=2,
                        bin_num=self._calculate_bin_for_user(user),
                    ))

            self.assertEqual(len(sent_messages), 1)

            # Load the site (which we query per message sent)
            # Check the schedule config
            with self.assertNumQueries(2):
                for args in sent_messages:
                    tasks._upgrade_reminder_schedule_send(*args)

            self.assertEqual(mock_channel.deliver.call_count, 1)
            for (_name, (_msg, email), _kwargs) in mock_channel.deliver.mock_calls:
                for template in attr.astuple(email):
                    self.assertNotIn("TEMPLATE WARNING", template)
                    self.assertNotIn("{{", template)
                    self.assertNotIn("}}", template)

    def _get_template_overrides(self):
        templates_override = deepcopy(settings.TEMPLATES)
        templates_override[0]['OPTIONS']['string_if_invalid'] = "TEMPLATE WARNING - MISSING VARIABLE [%s]"
        return templates_override

    def _calculate_bin_for_user(self, user):
        return user.id % resolvers.UPGRADE_REMINDER_NUM_BINS

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
