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
from mock import Mock, patch
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import CourseLocator

from openedx.core.djangoapps.schedules import resolvers, tasks
from openedx.core.djangoapps.schedules.management.commands import send_recurring_nudge as nudge
from openedx.core.djangoapps.schedules.tests.factories import ScheduleConfigFactory, ScheduleFactory
from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory, SiteFactory
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms
from student.tests.factories import UserFactory


@ddt.ddt
@skip_unless_lms
@skipUnless('openedx.core.djangoapps.schedules.apps.SchedulesConfig' in settings.INSTALLED_APPS,
            "Can't test schedules if the app isn't installed")
class TestSendRecurringNudge(CacheIsolationTestCase):
    # pylint: disable=protected-access

    def setUp(self):
        super(TestSendRecurringNudge, self).setUp()

        ScheduleFactory.create(start=datetime.datetime(2017, 8, 1, 15, 44, 30, tzinfo=pytz.UTC))
        ScheduleFactory.create(start=datetime.datetime(2017, 8, 1, 17, 34, 30, tzinfo=pytz.UTC))
        ScheduleFactory.create(start=datetime.datetime(2017, 8, 2, 15, 34, 30, tzinfo=pytz.UTC))

        site = SiteFactory.create()
        self.site_config = SiteConfigurationFactory.create(site=site)
        ScheduleConfigFactory.create(site=self.site_config.site)

    @patch.object(nudge.Command, 'resolver_class')
    def test_handle(self, mock_resolver):
        test_time = datetime.datetime(2017, 8, 1, tzinfo=pytz.UTC)
        nudge.Command().handle(date='2017-08-01', site_domain_name=self.site_config.site.domain)
        mock_resolver.assert_called_with(self.site_config.site, test_time)

        for day in (-3, -10):
            mock_resolver().send.assert_any_call(day, None)

    @patch.object(tasks, 'ace')
    @patch.object(resolvers.ScheduleStartResolver, 'async_send_task')
    def test_resolver_send(self, mock_schedule_bin, mock_ace):
        current_time = datetime.datetime(2017, 8, 1, tzinfo=pytz.UTC)
        nudge.ScheduleStartResolver(self.site_config.site, current_time).send(-3)
        test_time = current_time + datetime.timedelta(days=-3)
        self.assertFalse(mock_schedule_bin.called)
        mock_schedule_bin.apply_async.assert_any_call(
            (self.site_config.site.id, serialize(test_time), -3, 0, [], True, None),
            retry=False,
        )
        mock_schedule_bin.apply_async.assert_any_call(
            (self.site_config.site.id, serialize(test_time), -3, tasks.RECURRING_NUDGE_NUM_BINS - 1, [], True, None),
            retry=False,
        )
        self.assertFalse(mock_ace.send.called)

    @ddt.data(1, 10, 100)
    @patch.object(tasks, 'ace')
    @patch.object(tasks, '_recurring_nudge_schedule_send')
    def test_schedule_bin(self, schedule_count, mock_schedule_send, mock_ace):
        schedules = [
            ScheduleFactory.create(
                start=datetime.datetime(2017, 8, 3, 18, 44, 30, tzinfo=pytz.UTC),
                enrollment__user=UserFactory.create(),
                enrollment__course__id=CourseLocator('edX', 'toy', 'Bin')
            ) for _ in range(schedule_count)
        ]

        test_time = datetime.datetime(2017, 8, 3, 18, tzinfo=pytz.UTC)
        test_time_str = serialize(test_time)
        for b in range(tasks.RECURRING_NUDGE_NUM_BINS):
            # waffle flag takes an extra query before it is cached
            with self.assertNumQueries(2 if b == 0 else 1):
                tasks.recurring_nudge_schedule_bin(
                    self.site_config.site.id, target_day_str=test_time_str, day_offset=-3, bin_num=b,
                    org_list=[schedules[0].enrollment.course.org],
                )
        self.assertEqual(mock_schedule_send.apply_async.call_count, schedule_count)
        self.assertFalse(mock_ace.send.called)

    @patch.object(tasks, '_recurring_nudge_schedule_send')
    def test_no_course_overview(self, mock_schedule_send):

        schedule = ScheduleFactory.create(
            start=datetime.datetime(2017, 8, 3, 20, 34, 30, tzinfo=pytz.UTC),
        )
        schedule.enrollment.course_id = CourseKey.from_string('edX/toy/Not_2012_Fall')
        schedule.enrollment.save()

        test_time = datetime.datetime(2017, 8, 3, 20, tzinfo=pytz.UTC)
        test_time_str = serialize(test_time)
        for b in range(tasks.RECURRING_NUDGE_NUM_BINS):
            # waffle flag takes an extra query before it is cached
            with self.assertNumQueries(2 if b == 0 else 1):
                tasks.recurring_nudge_schedule_bin(
                    self.site_config.site.id, target_day_str=test_time_str, day_offset=-3, bin_num=b,
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
        ScheduleConfigFactory.create(site=self.site_config.site, deliver_recurring_nudge=False)

        mock_msg = Mock()
        tasks._recurring_nudge_schedule_send(self.site_config.site.id, mock_msg)
        self.assertFalse(mock_ace.send.called)

    @patch.object(tasks, 'ace')
    @patch.object(resolvers.ScheduleStartResolver, 'async_send_task')
    def test_enqueue_disabled(self, mock_schedule_bin, mock_ace):
        ScheduleConfigFactory.create(site=self.site_config.site, enqueue_recurring_nudge=False)

        current_time = datetime.datetime(2017, 8, 1, tzinfo=pytz.UTC)
        nudge.ScheduleStartResolver(self.site_config.site, current_time).send(3)
        self.assertFalse(mock_schedule_bin.called)
        self.assertFalse(mock_schedule_bin.apply_async.called)
        self.assertFalse(mock_ace.send.called)

    @patch.object(tasks, 'ace')
    @patch.object(tasks, '_recurring_nudge_schedule_send')
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

        user1 = UserFactory.create(id=tasks.RECURRING_NUDGE_NUM_BINS)
        user2 = UserFactory.create(id=tasks.RECURRING_NUDGE_NUM_BINS * 2)

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

        test_time = datetime.datetime(2017, 8, 3, 17, tzinfo=pytz.UTC)
        test_time_str = serialize(test_time)
        with self.assertNumQueries(2):
            tasks.recurring_nudge_schedule_bin(
                limited_config.site.id, target_day_str=test_time_str, day_offset=-3, bin_num=0,
                org_list=org_list, exclude_orgs=exclude_orgs,
            )

        self.assertEqual(mock_schedule_send.apply_async.call_count, expected_message_count)
        self.assertFalse(mock_ace.send.called)

    @patch.object(tasks, 'ace')
    @patch.object(tasks, '_recurring_nudge_schedule_send')
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

        test_time = datetime.datetime(2017, 8, 3, 19, 44, 30, tzinfo=pytz.UTC)
        test_time_str = serialize(test_time)
        with self.assertNumQueries(2):
            tasks.recurring_nudge_schedule_bin(
                self.site_config.site.id, target_day_str=test_time_str, day_offset=-3,
                bin_num=user.id % tasks.RECURRING_NUDGE_NUM_BINS,
                org_list=[schedules[0].enrollment.course.org],
            )
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

        test_time = datetime.datetime(2017, 8, 3, 19, tzinfo=pytz.UTC)
        test_time_str = serialize(test_time)

        patch_policies(self, [StubPolicy([ChannelType.PUSH])])
        mock_channel = Mock(
            name='test_channel',
            channel_type=ChannelType.EMAIL
        )
        patch_channels(self, [mock_channel])

        sent_messages = []

        templates_override = deepcopy(settings.TEMPLATES)
        templates_override[0]['OPTIONS']['string_if_invalid'] = "TEMPLATE WARNING - MISSING VARIABLE [%s]"
        with self.settings(TEMPLATES=templates_override):
            with patch.object(tasks, '_recurring_nudge_schedule_send') as mock_schedule_send:
                mock_schedule_send.apply_async = lambda args, *_a, **_kw: sent_messages.append(args)

                with self.assertNumQueries(2):
                    tasks.recurring_nudge_schedule_bin(
                        self.site_config.site.id, target_day_str=test_time_str, day_offset=day,
                        bin_num=user.id % tasks.RECURRING_NUDGE_NUM_BINS, org_list=[schedules[0].enrollment.course.org],
                    )

            self.assertEqual(len(sent_messages), 1)

            for args in sent_messages:
                tasks._recurring_nudge_schedule_send(*args)

            self.assertEqual(mock_channel.deliver.call_count, 1)
            for (_name, (_msg, email), _kwargs) in mock_channel.deliver.mock_calls:
                for template in attr.astuple(email):
                    self.assertNotIn("TEMPLATE WARNING", template)
