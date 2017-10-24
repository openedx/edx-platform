import datetime
from copy import deepcopy
import logging
from unittest import skipUnless

import attr
import ddt
import pytz
from django.conf import settings
from edx_ace import Message
from freezegun import freeze_time
from edx_ace.channel import ChannelType
from edx_ace.test_utils import StubPolicy, patch_channels, patch_policies
from edx_ace.utils.date import serialize
from mock import Mock, patch
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import CourseLocator

from course_modes.models import CourseMode
from course_modes.tests.factories import CourseModeFactory
from courseware.models import DynamicUpgradeDeadlineConfiguration
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.schedules import resolvers, tasks
from openedx.core.djangoapps.schedules.management.commands import send_upgrade_reminder as reminder
from openedx.core.djangoapps.schedules.tests.factories import ScheduleConfigFactory, ScheduleFactory
from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory, SiteFactory
from openedx.core.djangoapps.waffle_utils.testutils import WAFFLE_TABLES
from openedx.core.djangolib.testing.utils import skip_unless_lms
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


SITE_QUERY = 1
SCHEDULES_QUERY = 1
COURSE_MODES_QUERY = 1
GLOBAL_DEADLINE_SWITCH_QUERY = 1
COMMERCE_CONFIG_QUERY = 1

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
@freeze_time('2017-08-01 00:00:00', tz_offset=0, tick=True)
class TestUpgradeReminder(SharedModuleStoreTestCase):

    ENABLED_CACHES = ['default']

    @classmethod
    def setUpClass(cls):
        super(TestUpgradeReminder, cls).setUpClass()

        cls.course = CourseFactory.create(
            org='edX',
            number='test',
            display_name='Test Course',
            self_paced=True,
            start=datetime.datetime.now(pytz.UTC) - datetime.timedelta(days=30),
        )
        cls.course_overview = CourseOverview.get_from_id(cls.course.id)

    def setUp(self):
        super(TestUpgradeReminder, self).setUp()

        CourseModeFactory(
            course_id=self.course.id,
            mode_slug=CourseMode.VERIFIED,
            expiration_datetime=datetime.datetime.now(pytz.UTC) + datetime.timedelta(days=30),
        )

        ScheduleFactory.create(upgrade_deadline=datetime.datetime(2017, 8, 1, 15, 44, 30, tzinfo=pytz.UTC))
        ScheduleFactory.create(upgrade_deadline=datetime.datetime(2017, 8, 1, 17, 34, 30, tzinfo=pytz.UTC))
        ScheduleFactory.create(upgrade_deadline=datetime.datetime(2017, 8, 2, 15, 34, 30, tzinfo=pytz.UTC))

        site = SiteFactory.create()
        self.site_config = SiteConfigurationFactory.create(site=site)
        ScheduleConfigFactory.create(site=self.site_config.site)

        DynamicUpgradeDeadlineConfiguration.objects.create(enabled=True)

    @patch.object(reminder.Command, 'async_send_task')
    def test_handle(self, mock_send):
        test_day = datetime.datetime(2017, 8, 1, tzinfo=pytz.UTC)
        reminder.Command().handle(date='2017-08-01', site_domain_name=self.site_config.site.domain)
        mock_send.enqueue.assert_called_with(
            self.site_config.site,
            test_day,
            2,
            None
        )

    @patch.object(tasks, 'ace')
    def test_resolver_send(self, mock_ace):
        current_day = datetime.datetime(2017, 8, 1, tzinfo=pytz.UTC)
        test_day = current_day + datetime.timedelta(days=2)
        ScheduleFactory.create(upgrade_deadline=datetime.datetime(2017, 8, 3, 15, 34, 30, tzinfo=pytz.UTC))

        with patch.object(tasks.ScheduleUpgradeReminder, 'apply_async') as mock_apply_async:
            tasks.ScheduleUpgradeReminder.enqueue(self.site_config.site, current_day, 2)
            mock_apply_async.assert_any_call(
                (self.site_config.site.id, serialize(test_day), 2, 0, [], True, None),
                retry=False,
            )
            mock_apply_async.assert_any_call(
                (self.site_config.site.id, serialize(test_day), 2, resolvers.UPGRADE_REMINDER_NUM_BINS - 1, [], True, None),
                retry=False,
            )
            self.assertFalse(mock_ace.send.called)

    @ddt.data(1, 10, 100)
    @patch.object(tasks, 'ace')
    @patch.object(tasks.ScheduleUpgradeReminder, 'async_send_task')
    def test_schedule_bin(self, schedule_count, mock_schedule_send, mock_ace):
        upgrade_deadline = datetime.datetime.now(pytz.UTC) + datetime.timedelta(days=2)
        schedules = [
            ScheduleFactory.create(
                upgrade_deadline=upgrade_deadline,
                enrollment__course=self.course_overview,
            ) for i in range(schedule_count)
        ]

        bins_in_use = frozenset((s.enrollment.user.id % resolvers.UPGRADE_REMINDER_NUM_BINS) for s in schedules)
        is_first_match = True

        course_switch_queries = len(set(s.enrollment.course.id for s in schedules))

        test_datetime = datetime.datetime(upgrade_deadline.year, upgrade_deadline.month, upgrade_deadline.day, 18,
                                          tzinfo=pytz.UTC)
        test_datetime_str = serialize(test_datetime)

        for b in range(resolvers.UPGRADE_REMINDER_NUM_BINS):
            LOG.debug('Running bin %d', b)
            expected_queries = NUM_QUERIES_NO_MATCHING_SCHEDULES
            if b in bins_in_use:
                if is_first_match:
                    expected_queries = (
                        # Since this is the first match, we need to cache all of the config models, so we run a query
                        # for each of those...
                        NUM_QUERIES_FIRST_MATCH
                        + course_switch_queries
                    )
                    is_first_match = False
                else:
                    expected_queries = NUM_QUERIES_WITH_MATCHES

            with self.assertNumQueries(expected_queries, table_blacklist=WAFFLE_TABLES):
                tasks.ScheduleUpgradeReminder.delay(
                    self.site_config.site.id, target_day_str=test_datetime_str, day_offset=2, bin_num=b,
                    org_list=[schedules[0].enrollment.course.org],
                )

        self.assertEqual(mock_schedule_send.apply_async.call_count, schedule_count)
        self.assertFalse(mock_ace.send.called)

    @patch.object(tasks.ScheduleUpgradeReminder, 'async_send_task')
    def test_no_course_overview(self, mock_schedule_send):

        schedule = ScheduleFactory.create(
            upgrade_deadline=datetime.datetime(2017, 8, 3, 20, 34, 30, tzinfo=pytz.UTC),
        )
        schedule.enrollment.course_id = CourseKey.from_string('edX/toy/Not_2012_Fall')
        schedule.enrollment.save()

        test_datetime = datetime.datetime(2017, 8, 3, 20, tzinfo=pytz.UTC)
        test_datetime_str = serialize(test_datetime)
        for b in range(resolvers.UPGRADE_REMINDER_NUM_BINS):
            with self.assertNumQueries(NUM_QUERIES_NO_MATCHING_SCHEDULES, table_blacklist=WAFFLE_TABLES):
                tasks.ScheduleUpgradeReminder.delay(
                    self.site_config.site.id, target_day_str=test_datetime_str, day_offset=2, bin_num=b,
                    org_list=[schedule.enrollment.course.org],
                )

        # There is no database constraint that enforces that enrollment.course_id points
        # to a valid CourseOverview object. However, in that case, schedules isn't going
        # to attempt to address it, and will instead simply skip those users.
        # This happens 'transparently' because django generates an inner-join between
        # enrollment and course_overview, and thus will skip any rows where course_overview
        # is null.
        self.assertEqual(mock_schedule_send.apply_async.call_count, 0)

    @patch.object(tasks, 'ace')
    def test_delivery_disabled(self, mock_ace):
        ScheduleConfigFactory.create(site=self.site_config.site, deliver_upgrade_reminder=False)

        mock_msg = Mock()
        tasks._upgrade_reminder_schedule_send(self.site_config.site.id, mock_msg)
        self.assertFalse(mock_ace.send.called)

    @patch.object(tasks, 'ace')
    @patch.object(tasks.ScheduleUpgradeReminder, 'apply_async')
    def test_enqueue_disabled(self, mock_ace, mock_apply_async):
        ScheduleConfigFactory.create(site=self.site_config.site, enqueue_upgrade_reminder=False)

        current_day = datetime.datetime(2017, 8, 1, tzinfo=pytz.UTC)
        tasks.ScheduleUpgradeReminder.enqueue(
            self.site_config.site,
            current_day,
            day_offset=3,
        )
        self.assertFalse(mock_apply_async.called)
        self.assertFalse(mock_ace.send.called)

    @patch.object(tasks, 'ace')
    @patch.object(tasks.ScheduleUpgradeReminder, 'async_send_task')
    @ddt.data(
        ((['filtered_org'], False, 1)),
        ((['filtered_org'], True, 2))
    )
    @ddt.unpack
    def test_site_config(self, org_list, exclude_orgs, expected_message_count, mock_schedule_send, mock_ace):
        filtered_org = 'filtered_org'
        unfiltered_org = 'unfiltered_org'
        site1 = SiteFactory.create(domain='foo1.bar', name='foo1.bar')
        limited_config = SiteConfigurationFactory.create(values={'course_org_filter': [filtered_org]}, site=site1)
        site2 = SiteFactory.create(domain='foo2.bar', name='foo2.bar')
        unlimited_config = SiteConfigurationFactory.create(values={'course_org_filter': []}, site=site2)

        for config in (limited_config, unlimited_config):
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
        with self.assertNumQueries(NUM_QUERIES_FIRST_MATCH + course_switch_queries, table_blacklist=WAFFLE_TABLES):
            tasks.ScheduleUpgradeReminder.delay(
                limited_config.site.id, target_day_str=test_datetime_str, day_offset=2, bin_num=0,
                org_list=org_list, exclude_orgs=exclude_orgs,
            )

        self.assertEqual(mock_schedule_send.apply_async.call_count, expected_message_count)
        self.assertFalse(mock_ace.send.called)

    @patch.object(tasks, 'ace')
    @patch.object(tasks.ScheduleUpgradeReminder, 'async_send_task')
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

        num_courses = len(set(s.enrollment.course.id for s in schedules))

        test_datetime = datetime.datetime(2017, 8, 3, 19, 44, 30, tzinfo=pytz.UTC)
        test_datetime_str = serialize(test_datetime)

        with self.assertNumQueries(NUM_QUERIES_FIRST_MATCH + num_courses, table_blacklist=WAFFLE_TABLES):
            tasks.ScheduleUpgradeReminder.delay(
                self.site_config.site.id, target_day_str=test_datetime_str, day_offset=2,
                bin_num=user.id % resolvers.UPGRADE_REMINDER_NUM_BINS,
                org_list=[schedules[0].enrollment.course.org],
            )
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

        num_courses = len(set(s.enrollment.course.id for s in schedules))

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
            with patch.object(tasks.ScheduleUpgradeReminder, 'async_send_task') as mock_schedule_send:
                mock_schedule_send.apply_async = lambda args, *_a, **_kw: sent_messages.append(args)

                # we execute one query per course to see if it's opted out of dynamic upgrade deadlines
                num_expected_queries = NUM_QUERIES_FIRST_MATCH + num_courses
                with self.assertNumQueries(num_expected_queries, table_blacklist=WAFFLE_TABLES):
                    tasks.ScheduleUpgradeReminder.delay(
                        self.site_config.site.id, target_day_str=test_datetime_str, day_offset=2,
                        bin_num=self._calculate_bin_for_user(user),
                        org_list=[schedules[0].enrollment.course.org],
                    )

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

        tasks.ScheduleUpgradeReminder.delay(
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
        bin_num = self._calculate_bin_for_user(user)

        sent_messages = []
        with patch.object(tasks.ScheduleUpgradeReminder, 'async_send_task') as mock_schedule_send:
            mock_schedule_send.apply_async = lambda args, *_a, **_kw: sent_messages.append(args[1])

            tasks.ScheduleUpgradeReminder.delay(
                self.site_config.site.id, target_day_str=test_datetime_str, day_offset=2, bin_num=bin_num,
                org_list=[schedules[0].enrollment.course.org],
            )

            messages = [Message.from_string(m) for m in sent_messages]
            self.assertEqual(len(messages), 1)
            message = messages[0]
            self.assertItemsEqual(
                message.context['course_ids'],
                [str(schedules[i].enrollment.course.id) for i in (1, 2, 4)]
            )
