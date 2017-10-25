import datetime
import itertools
from copy import deepcopy
from unittest import skipUnless

import attr
import ddt
import pytz
from django.conf import settings
from edx_ace.channel import ChannelType
from edx_ace.test_utils import StubPolicy, patch_channels, patch_policies
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
from openedx.core.djangoapps.schedules.tests.factories import ScheduleConfigFactory, ScheduleFactory
from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory, SiteFactory
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
class TestSendRecurringNudge(FilteredQueryCountMixin, CacheIsolationTestCase):
    # pylint: disable=protected-access

    ENABLED_CACHES = ['default']

    def setUp(self):
        super(TestSendRecurringNudge, self).setUp()

        ScheduleFactory.create(start=datetime.datetime(2017, 8, 1, 15, 44, 30, tzinfo=pytz.UTC))
        ScheduleFactory.create(start=datetime.datetime(2017, 8, 1, 17, 34, 30, tzinfo=pytz.UTC))
        ScheduleFactory.create(start=datetime.datetime(2017, 8, 2, 15, 34, 30, tzinfo=pytz.UTC))

        site = SiteFactory.create()
        self.site_config = SiteConfigurationFactory.create(site=site)
        ScheduleConfigFactory.create(site=self.site_config.site)

        DynamicUpgradeDeadlineConfiguration.objects.create(enabled=True)

    @patch.object(nudge.Command, 'async_send_task')
    def test_handle(self, mock_send):
        test_day = datetime.datetime(2017, 8, 1, tzinfo=pytz.UTC)
        nudge.Command().handle(date='2017-08-01', site_domain_name=self.site_config.site.domain)
        for day in (-3, -10):
            mock_send.enqueue.assert_any_call(
                self.site_config.site,
                test_day,
                day,
                None
            )

    @patch.object(tasks, 'ace')
    def test_resolver_send(self, mock_ace):
        current_day = datetime.datetime(2017, 8, 1, tzinfo=pytz.UTC)
        with patch.object(tasks.ScheduleRecurringNudge, 'apply_async') as mock_apply_async:
            tasks.ScheduleRecurringNudge.enqueue(self.site_config.site, current_day, -3)
            test_day = current_day + datetime.timedelta(days=-3)
            mock_apply_async.assert_any_call(
                (self.site_config.site.id, serialize(test_day), -3, 0, None),
                retry=False,
            )
            mock_apply_async.assert_any_call(
                (self.site_config.site.id, serialize(test_day), -3, resolvers.RECURRING_NUDGE_NUM_BINS - 1, None),
                retry=False,
            )
            self.assertFalse(mock_ace.send.called)

    @ddt.data(1, 10, 100)
    @patch.object(tasks, 'ace')
    @patch.object(tasks.ScheduleRecurringNudge, 'async_send_task')
    def test_schedule_bin(self, schedule_count, mock_schedule_send, mock_ace):
        schedules = [
            ScheduleFactory.create(
                start=datetime.datetime(2017, 8, 3, 18, 44, 30, tzinfo=pytz.UTC),
                enrollment__course__id=CourseLocator('edX', 'toy', 'Bin')
            ) for i in range(schedule_count)
        ]

        bins_in_use = frozenset((s.enrollment.user.id % resolvers.RECURRING_NUDGE_NUM_BINS) for s in schedules)

        test_datetime = datetime.datetime(2017, 8, 3, 18, tzinfo=pytz.UTC)
        test_datetime_str = serialize(test_datetime)
        for b in range(resolvers.RECURRING_NUDGE_NUM_BINS):
            expected_queries = NUM_QUERIES_NO_MATCHING_SCHEDULES + NUM_QUERIES_NO_ORG_LIST
            if b in bins_in_use:
                # to fetch course modes for valid schedules
                expected_queries += NUM_COURSE_MODES_QUERIES

            with self.assertNumQueries(expected_queries, table_blacklist=WAFFLE_TABLES):

                tasks.ScheduleRecurringNudge.apply(kwargs=dict(
                    site_id=self.site_config.site.id, target_day_str=test_datetime_str, day_offset=-3, bin_num=b,
                ))
        self.assertEqual(mock_schedule_send.apply_async.call_count, schedule_count)
        self.assertFalse(mock_ace.send.called)

    @patch.object(tasks.ScheduleRecurringNudge, 'async_send_task')
    def test_no_course_overview(self, mock_schedule_send):
        schedule = ScheduleFactory.create(
            start=datetime.datetime(2017, 8, 3, 20, 34, 30, tzinfo=pytz.UTC),
            enrollment__user=UserFactory.create(),
        )
        schedule.enrollment.course_id = CourseKey.from_string('edX/toy/Not_2012_Fall')
        schedule.enrollment.save()

        test_datetime = datetime.datetime(2017, 8, 3, 20, tzinfo=pytz.UTC)
        test_datetime_str = serialize(test_datetime)
        for b in range(resolvers.RECURRING_NUDGE_NUM_BINS):
            with self.assertNumQueries(NUM_QUERIES_NO_MATCHING_SCHEDULES + NUM_QUERIES_NO_ORG_LIST, table_blacklist=WAFFLE_TABLES):
                tasks.ScheduleRecurringNudge.apply(kwargs=dict(
                    site_id=self.site_config.site.id, target_day_str=test_datetime_str, day_offset=-3, bin_num=b
                ))

        # There is no database constraint that enforces that enrollment.course_id points
        # to a valid CourseOverview object. However, in that case, schedules isn't going
        # to attempt to address it, and will instead simply skip those users.
        # This happens 'transparently' because django generates an inner-join between
        # enrollment and course_overview, and thus will skip any rows where course_overview
        # is null.
        self.assertEqual(mock_schedule_send.apply_async.call_count, 0)

    @patch.object(tasks.ScheduleRecurringNudge, 'async_send_task')
    def test_send_after_course_end(self, mock_schedule_send):
        user1 = UserFactory.create(id=resolvers.RECURRING_NUDGE_NUM_BINS)

        schedule_start = datetime.datetime(2017, 8, 3, 20, 34, 30, tzinfo=pytz.UTC)
        day_command_is_run = schedule_start + datetime.timedelta(days=3)
        schedule = ScheduleFactory.create(
            start=schedule_start,
            enrollment__user=user1,
        )

        schedule.enrollment.course.start = schedule_start - datetime.timedelta(days=30)
        schedule.enrollment.course.end = day_command_is_run - datetime.timedelta(days=1)
        schedule.enrollment.course.save()

        test_datetime = datetime.datetime(2017, 8, 3, 20, tzinfo=pytz.UTC)
        test_datetime_str = serialize(test_datetime)

        tasks.ScheduleRecurringNudge.apply(kwargs=dict(
            site_id=self.site_config.site.id, target_day_str=test_datetime_str, day_offset=-3, bin_num=0,
        ))

        self.assertFalse(mock_schedule_send.apply_async.called)

    @patch.object(tasks, 'ace')
    def test_delivery_disabled(self, mock_ace):
        ScheduleConfigFactory.create(site=self.site_config.site, deliver_recurring_nudge=False)

        mock_msg = Mock()
        tasks._recurring_nudge_schedule_send(self.site_config.site.id, mock_msg)
        self.assertFalse(mock_ace.send.called)

    @patch.object(tasks, 'ace')
    @patch.object(tasks.ScheduleUpgradeReminder, 'apply_async')
    def test_enqueue_disabled(self, mock_ace, mock_apply_async):
        ScheduleConfigFactory.create(site=self.site_config.site, enqueue_recurring_nudge=False)

        current_datetime = datetime.datetime(2017, 8, 1, tzinfo=pytz.UTC)
        tasks.ScheduleRecurringNudge.enqueue(
            self.site_config.site,
            current_datetime,
            3
        )
        self.assertFalse(mock_apply_async.called)
        self.assertFalse(mock_ace.send.called)

    @patch.object(tasks, 'ace')
    @patch.object(tasks.ScheduleRecurringNudge, 'async_send_task')
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

        user1 = UserFactory.create(id=resolvers.RECURRING_NUDGE_NUM_BINS)
        user2 = UserFactory.create(id=resolvers.RECURRING_NUDGE_NUM_BINS * 2)

        ScheduleFactory.create(
            start=datetime.datetime(2017, 8, 3, 17, 44, 30, tzinfo=pytz.UTC),
            enrollment__course__org=filtered_org,
            enrollment__user=user1,
        )
        ScheduleFactory.create(
            start=datetime.datetime(2017, 8, 3, 17, 44, 30, tzinfo=pytz.UTC),
            enrollment__course__org=unfiltered_org,
            enrollment__user=user1,
        )
        ScheduleFactory.create(
            start=datetime.datetime(2017, 8, 3, 17, 44, 30, tzinfo=pytz.UTC),
            enrollment__course__org=unfiltered_org,
            enrollment__user=user2,
        )

        test_datetime = datetime.datetime(2017, 8, 3, 17, tzinfo=pytz.UTC)
        test_datetime_str = serialize(test_datetime)

        expected_queries = NUM_QUERIES_WITH_MATCHES
        if not this_org_list:
            expected_queries += NUM_QUERIES_NO_ORG_LIST

        with self.assertNumQueries(expected_queries, table_blacklist=WAFFLE_TABLES):
            tasks.ScheduleRecurringNudge.apply(kwargs=dict(
                site_id=this_config.site.id, target_day_str=test_datetime_str, day_offset=-3, bin_num=0
            ))

        self.assertEqual(mock_schedule_send.apply_async.call_count, expected_message_count)
        self.assertFalse(mock_ace.send.called)

    @patch.object(tasks, 'ace')
    @patch.object(tasks.ScheduleRecurringNudge, 'async_send_task')
    def test_multiple_enrollments(self, mock_schedule_send, mock_ace):
        user = UserFactory.create()
        schedules = [
            ScheduleFactory.create(
                start=datetime.datetime(2017, 8, 3, 19, 44, 30, tzinfo=pytz.UTC),
                enrollment__user=user,
                enrollment__course__id=CourseLocator('edX', 'toy', 'Course{}'.format(course_num))
            )
            for course_num in (1, 2, 3)
        ]

        test_datetime = datetime.datetime(2017, 8, 3, 19, 44, 30, tzinfo=pytz.UTC)
        test_datetime_str = serialize(test_datetime)
        with self.assertNumQueries(NUM_QUERIES_WITH_MATCHES + NUM_QUERIES_NO_ORG_LIST, table_blacklist=WAFFLE_TABLES):
            tasks.ScheduleRecurringNudge.apply(kwargs=dict(
                site_id=self.site_config.site.id, target_day_str=test_datetime_str, day_offset=-3,
                bin_num=user.id % resolvers.RECURRING_NUDGE_NUM_BINS,
            ))
        self.assertEqual(mock_schedule_send.apply_async.call_count, 1)
        self.assertFalse(mock_ace.send.called)

    @ddt.data(*itertools.product((1, 10, 100), (-3, -10)))
    @ddt.unpack
    def test_templates(self, message_count, day):

        user = UserFactory.create()
        schedules = [
            ScheduleFactory.create(
                start=datetime.datetime(2017, 8, 3, 19, 44, 30, tzinfo=pytz.UTC),
                enrollment__user=user,
                enrollment__course__id=CourseLocator('edX', 'toy', 'Course{}'.format(course_num))
            )
            for course_num in range(message_count)
        ]

        test_datetime = datetime.datetime(2017, 8, 3, 19, tzinfo=pytz.UTC)
        test_datetime_str = serialize(test_datetime)

        patch_policies(self, [StubPolicy([ChannelType.PUSH])])
        mock_channel = Mock(
            name='test_channel',
            channel_type=ChannelType.EMAIL
        )
        patch_channels(self, [mock_channel])

        sent_messages = []

        with self.settings(TEMPLATES=self._get_template_overrides()):
            with patch.object(tasks.ScheduleRecurringNudge, 'async_send_task') as mock_schedule_send:
                mock_schedule_send.apply_async = lambda args, *_a, **_kw: sent_messages.append(args)

                with self.assertNumQueries(NUM_QUERIES_WITH_MATCHES + NUM_QUERIES_NO_ORG_LIST, table_blacklist=WAFFLE_TABLES):
                    tasks.ScheduleRecurringNudge.apply(kwargs=dict(
                        site_id=self.site_config.site.id, target_day_str=test_datetime_str, day_offset=day,
                        bin_num=self._calculate_bin_for_user(user),
                    ))

            self.assertEqual(len(sent_messages), 1)

            # Load the site
            # Check the schedule config
            with self.assertNumQueries(2):
                for args in sent_messages:
                    tasks._recurring_nudge_schedule_send(*args)

            self.assertEqual(mock_channel.deliver.call_count, 1)
            for (_name, (_msg, email), _kwargs) in mock_channel.deliver.mock_calls:
                for template in attr.astuple(email):
                    self.assertNotIn("TEMPLATE WARNING", template)
                    self.assertNotIn("{{", template)
                    self.assertNotIn("}}", template)

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
        sent_messages = self._stub_sender_and_collect_sent_messages(bin_task=tasks.ScheduleRecurringNudge,
                                                                    stubbed_send_task=patch.object(tasks.ScheduleRecurringNudge, 'async_send_task'),
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
        sent_messages = self._stub_sender_and_collect_sent_messages(bin_task=tasks.ScheduleRecurringNudge,
                                                                    stubbed_send_task=patch.object(tasks.ScheduleRecurringNudge, 'async_send_task'),
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
        sent_messages = self._stub_sender_and_collect_sent_messages(bin_task=tasks.ScheduleRecurringNudge,
                                                                    stubbed_send_task=patch.object(tasks.ScheduleRecurringNudge, 'async_send_task'),
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

    def _get_template_overrides(self):
        templates_override = deepcopy(settings.TEMPLATES)
        templates_override[0]['OPTIONS']['string_if_invalid'] = "TEMPLATE WARNING - MISSING VARIABLE [%s]"
        return templates_override

    def _calculate_bin_for_user(self, user):
        return user.id % resolvers.RECURRING_NUDGE_NUM_BINS

    def _contains_upsell_attribute(self, msg_attr):
        msg = Message.from_string(msg_attr)
        tmp = msg.context["show_upsell"]
        return msg.context["show_upsell"]
