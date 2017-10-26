from copy import deepcopy
import datetime
import ddt
import logging

import attr
from django.conf import settings
from freezegun import freeze_time
from mock import Mock, patch
import pytz

from courseware.models import DynamicUpgradeDeadlineConfiguration
from edx_ace.channel import ChannelType
from edx_ace.utils.date import serialize
from edx_ace.test_utils import StubPolicy, patch_channels, patch_policies
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory, SiteFactory
from openedx.core.djangoapps.schedules import resolvers, tasks
from openedx.core.djangoapps.schedules.resolvers import _get_datetime_beginning_of_day
from openedx.core.djangoapps.schedules.tests.factories import ScheduleConfigFactory, ScheduleFactory
from openedx.core.djangoapps.waffle_utils.testutils import WAFFLE_TABLES
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase


SITE_QUERY = 1
ORG_DEADLINE_QUERY = 1
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
    + ORG_DEADLINE_QUERY
    + COMMERCE_CONFIG_QUERY
)

LOG = logging.getLogger(__name__)


@ddt.ddt
@freeze_time('2017-08-01 00:00:00', tz_offset=0, tick=True)
class ScheduleBaseEmailTestBase(SharedModuleStoreTestCase):

    __test__ = False

    ENABLED_CACHES = ['default']

    has_course_queries = False

    def setUp(self):
        super(ScheduleBaseEmailTestBase, self).setUp()

        site = SiteFactory.create()
        self.site_config = SiteConfigurationFactory.create(site=site)
        ScheduleConfigFactory.create(site=self.site_config.site)

        DynamicUpgradeDeadlineConfiguration.objects.create(enabled=True)

    def _calculate_bin_for_user(self, user):
        return user.id % self.tested_task.num_bins

    def _get_dates(self, offset=None):
        current_day = _get_datetime_beginning_of_day(datetime.datetime.now(pytz.UTC))
        offset = offset or self.expected_offsets[0]
        target_day = current_day + datetime.timedelta(days=offset)
        return current_day, offset, target_day

    def _get_template_overrides(self):
        templates_override = deepcopy(settings.TEMPLATES)
        templates_override[0]['OPTIONS']['string_if_invalid'] = "TEMPLATE WARNING - MISSING VARIABLE [%s]"
        return templates_override

    def test_command_task_binding(self):
        self.assertEqual(self.tested_command.async_send_task, self.tested_task)

    def test_handle(self):
        with patch.object(self.tested_command, 'async_send_task') as mock_send:
            test_day = datetime.datetime(2017, 8, 1, tzinfo=pytz.UTC)
            self.tested_command().handle(date='2017-08-01', site_domain_name=self.site_config.site.domain)

            for offset in self.expected_offsets:
                mock_send.enqueue.assert_any_call(
                    self.site_config.site,
                    test_day,
                    offset,
                    None
                )

    @patch.object(tasks, 'ace')
    def test_resolver_send(self, mock_ace):
        current_day, offset, target_day = self._get_dates()
        with patch.object(self.tested_task, 'apply_async') as mock_apply_async:
            self.tested_task.enqueue(self.site_config.site, current_day, offset)
        mock_apply_async.assert_any_call(
            (self.site_config.site.id, serialize(target_day), offset, 0, None),
            retry=False,
        )
        mock_apply_async.assert_any_call(
            (self.site_config.site.id, serialize(target_day), offset, self.tested_task.num_bins - 1, None),
            retry=False,
        )
        self.assertFalse(mock_ace.send.called)

    @ddt.data(1, 10, 100)
    @patch.object(tasks, 'ace')
    @patch.object(resolvers, 'set_custom_metric')
    def test_schedule_bin(self, schedule_count, mock_metric, mock_ace):
        with patch.object(self.tested_task, 'async_send_task') as mock_schedule_send:
            current_day, offset, target_day = self._get_dates()
            schedules = [
                ScheduleFactory.create(
                    start=target_day,
                    upgrade_deadline=target_day,
                    enrollment__course__self_paced=True,
                ) for _ in range(schedule_count)
            ]

            bins_in_use = frozenset((self._calculate_bin_for_user(s.enrollment.user)) for s in schedules)
            is_first_match = True
            course_queries = len(set(s.enrollment.course.id for s in schedules)) if self.has_course_queries else 0
            target_day_str = serialize(target_day)

            for b in range(self.tested_task.num_bins):
                LOG.debug('Running bin %d', b)
                expected_queries = NUM_QUERIES_NO_MATCHING_SCHEDULES
                if b in bins_in_use:
                    if is_first_match:
                        expected_queries = (
                            # Since this is the first match, we need to cache all of the config models, so we run a
                            # query for each of those...
                            NUM_QUERIES_FIRST_MATCH + course_queries
                        )
                        is_first_match = False
                    else:
                        expected_queries = NUM_QUERIES_WITH_MATCHES

                expected_queries += NUM_QUERIES_NO_ORG_LIST

                with self.assertNumQueries(expected_queries, table_blacklist=WAFFLE_TABLES):
                    self.tested_task.apply(kwargs=dict(
                        site_id=self.site_config.site.id, target_day_str=target_day_str, day_offset=offset, bin_num=b,
                    ))

                num_schedules = mock_metric.call_args[0][1]
                if b in bins_in_use:
                    self.assertGreater(num_schedules, 0)
                else:
                    self.assertEqual(num_schedules, 0)

            self.assertEqual(mock_schedule_send.apply_async.call_count, schedule_count)
            self.assertFalse(mock_ace.send.called)

    def test_no_course_overview(self):
        current_day, offset, target_day = self._get_dates()
        schedule = ScheduleFactory.create(
            start=target_day,
            upgrade_deadline=target_day,
            enrollment__course__self_paced=True,
        )
        schedule.enrollment.course_id = CourseKey.from_string('edX/toy/Not_2012_Fall')
        schedule.enrollment.save()

        with patch.object(self.tested_task, 'async_send_task') as mock_schedule_send:
            for b in range(self.tested_task.num_bins):
                self.tested_task.apply(kwargs=dict(
                    site_id=self.site_config.site.id,
                    target_day_str=serialize(target_day),
                    day_offset=offset,
                    bin_num=b,
                ))

        # There is no database constraint that enforces that enrollment.course_id points
        # to a valid CourseOverview object. However, in that case, schedules isn't going
        # to attempt to address it, and will instead simply skip those users.
        # This happens 'transparently' because django generates an inner-join between
        # enrollment and course_overview, and thus will skip any rows where course_overview
        # is null.
        self.assertEqual(mock_schedule_send.apply_async.call_count, 0)

    @ddt.data(True, False)
    @patch.object(tasks, 'ace')
    @patch.object(tasks, 'Message')
    def test_deliver_config(self, is_enabled, mock_message, mock_ace):
        schedule_config_kwargs = {
            'site': self.site_config.site,
            self.deliver_config: is_enabled,
        }
        ScheduleConfigFactory.create(**schedule_config_kwargs)

        mock_msg = Mock()
        self.deliver_task(self.site_config.site.id, mock_msg)
        if is_enabled:
            self.assertTrue(mock_ace.send.called)
        else:
            self.assertFalse(mock_ace.send.called)

    @ddt.data(True, False)
    def test_enqueue_config(self, is_enabled):
        schedule_config_kwargs = {
            'site': self.site_config.site,
            self.enqueue_config: is_enabled,
        }
        ScheduleConfigFactory.create(**schedule_config_kwargs)

        current_datetime = datetime.datetime(2017, 8, 1, tzinfo=pytz.UTC)
        with patch.object(self.tested_task, 'apply_async') as mock_apply_async:
            self.tested_task.enqueue(self.site_config.site, current_datetime, 3)

        if is_enabled:
            self.assertTrue(mock_apply_async.called)
        else:
            self.assertFalse(mock_apply_async.called)

    @patch.object(tasks, 'ace')
    @ddt.data(
        ((['filtered_org'], [], 1)),
        (([], ['filtered_org'], 2))
    )
    @ddt.unpack
    def test_site_config(self, this_org_list, other_org_list, expected_message_count, mock_ace):
        filtered_org = 'filtered_org'
        unfiltered_org = 'unfiltered_org'
        this_config = SiteConfigurationFactory.create(values={'course_org_filter': this_org_list})
        other_config = SiteConfigurationFactory.create(values={'course_org_filter': other_org_list})

        for config in (this_config, other_config):
            ScheduleConfigFactory.create(site=config.site)

        user1 = UserFactory.create(id=self.tested_task.num_bins)
        user2 = UserFactory.create(id=self.tested_task.num_bins * 2)
        current_day, offset, target_day = self._get_dates()

        ScheduleFactory.create(
            upgrade_deadline=target_day,
            start=target_day,
            enrollment__course__org=filtered_org,
            enrollment__course__self_paced=True,
            enrollment__user=user1,
        )
        ScheduleFactory.create(
            upgrade_deadline=target_day,
            start=target_day,
            enrollment__course__org=unfiltered_org,
            enrollment__course__self_paced=True,
            enrollment__user=user1,
        )
        ScheduleFactory.create(
            upgrade_deadline=target_day,
            start=target_day,
            enrollment__course__org=unfiltered_org,
            enrollment__course__self_paced=True,
            enrollment__user=user2,
        )

        with patch.object(self.tested_task, 'async_send_task') as mock_schedule_send:
            self.tested_task.apply(kwargs=dict(
                site_id=this_config.site.id, target_day_str=serialize(target_day), day_offset=offset, bin_num=0
            ))

        self.assertEqual(mock_schedule_send.apply_async.call_count, expected_message_count)
        self.assertFalse(mock_ace.send.called)

    @ddt.data(True, False)
    def test_course_end(self, has_course_ended):
        user1 = UserFactory.create(id=self.tested_task.num_bins)
        current_day, offset, target_day = self._get_dates()

        schedule = ScheduleFactory.create(
            start=target_day,
            upgrade_deadline=target_day,
            enrollment__course__self_paced=True,
            enrollment__user=user1,
        )

        schedule.enrollment.course.start = current_day - datetime.timedelta(days=30)
        end_date_offset = -2 if has_course_ended else 2
        schedule.enrollment.course.end = current_day + datetime.timedelta(days=end_date_offset)
        schedule.enrollment.course.save()

        with patch.object(self.tested_task, 'async_send_task') as mock_schedule_send:
            self.tested_task.apply(kwargs=dict(
                site_id=self.site_config.site.id, target_day_str=serialize(target_day), day_offset=offset, bin_num=0,
            ))

        if has_course_ended:
            self.assertFalse(mock_schedule_send.apply_async.called)
        else:
            self.assertTrue(mock_schedule_send.apply_async.called)

    @patch.object(tasks, 'ace')
    def test_multiple_enrollments(self, mock_ace):
        user = UserFactory.create()
        current_day, offset, target_day = self._get_dates()
        num_courses = 3
        for course_index in range(num_courses):
            ScheduleFactory.create(
                start=target_day,
                upgrade_deadline=target_day,
                enrollment__course__self_paced=True,
                enrollment__user=user,
                enrollment__course__id=CourseKey.from_string('edX/toy/course{}'.format(course_index))
            )

        course_queries = num_courses if self.has_course_queries else 0
        expected_query_count = NUM_QUERIES_FIRST_MATCH + course_queries + NUM_QUERIES_NO_ORG_LIST
        with self.assertNumQueries(expected_query_count, table_blacklist=WAFFLE_TABLES):
            with patch.object(self.tested_task, 'async_send_task') as mock_schedule_send:
                self.tested_task.apply(kwargs=dict(
                    site_id=self.site_config.site.id, target_day_str=serialize(target_day), day_offset=offset,
                    bin_num=self._calculate_bin_for_user(user),
                ))
            self.assertEqual(mock_schedule_send.apply_async.call_count, 1)
            self.assertFalse(mock_ace.send.called)

    @ddt.data(1, 10, 100)
    def test_templates(self, message_count):
        for offset in self.expected_offsets:
            self._assert_template_for_offset(offset, message_count)
            self.clear_caches()

    def _assert_template_for_offset(self, offset, message_count):
        current_day, offset, target_day = self._get_dates(offset)

        user = UserFactory.create()
        for course_index in range(message_count):
            ScheduleFactory.create(
                start=target_day,
                upgrade_deadline=target_day,
                enrollment__course__self_paced=True,
                enrollment__user=user,
                enrollment__course__id=CourseKey.from_string('edX/toy/course{}'.format(course_index))
            )

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

                num_expected_queries = NUM_QUERIES_NO_ORG_LIST + NUM_QUERIES_FIRST_MATCH
                if self.has_course_queries:
                    num_expected_queries += message_count

                with self.assertNumQueries(num_expected_queries, table_blacklist=WAFFLE_TABLES):
                    self.tested_task.apply(kwargs=dict(
                        site_id=self.site_config.site.id, target_day_str=serialize(target_day), day_offset=offset,
                        bin_num=self._calculate_bin_for_user(user),
                    ))
            self.assertEqual(len(sent_messages), 1)

            with self.assertNumQueries(2):
                for args in sent_messages:
                    self.deliver_task(*args)

            self.assertEqual(mock_channel.deliver.call_count, 1)
            for (_name, (_msg, email), _kwargs) in mock_channel.deliver.mock_calls:
                for template in attr.astuple(email):
                    self.assertNotIn("TEMPLATE WARNING", template)
                    self.assertNotIn("{{", template)
                    self.assertNotIn("}}", template)
