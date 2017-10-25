import datetime
import ddt
import logging

from freezegun import freeze_time
from mock import patch
import pytz

from courseware.models import DynamicUpgradeDeadlineConfiguration
from edx_ace.utils.date import serialize
from opaque_keys.edx.locator import CourseLocator
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory, SiteFactory
from openedx.core.djangoapps.schedules import resolvers, tasks
from openedx.core.djangoapps.schedules.tests.factories import ScheduleConfigFactory, ScheduleFactory
from openedx.core.djangoapps.waffle_utils.testutils import WAFFLE_TABLES
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, FilteredQueryCountMixin
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


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
@freeze_time('2017-08-01 00:00:00', tz_offset=0, tick=True)
class ScheduleBaseEmailTestBase(SharedModuleStoreTestCase):

    __test__ = False

    ENABLED_CACHES = ['default']

    has_course_queries = False

    @classmethod
    def setUpClass(cls):
        super(ScheduleBaseEmailTestBase, cls).setUpClass()

        cls.course = CourseFactory.create(
            org='edX',
            number='test',
            display_name='Test Course',
            self_paced=True,
            start=datetime.datetime.now(pytz.UTC) - datetime.timedelta(days=30),
        )
        cls.course_overview = CourseOverview.get_from_id(cls.course.id)

    def setUp(self):
        super(ScheduleBaseEmailTestBase, self).setUp()

        site = SiteFactory.create()
        self.site_config = SiteConfigurationFactory.create(site=site)
        ScheduleConfigFactory.create(site=self.site_config.site)

        DynamicUpgradeDeadlineConfiguration.objects.create(enabled=True)

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
        current_day = datetime.datetime(2017, 8, 1, tzinfo=pytz.UTC)
        offset = self.expected_offsets[0]
        target_day = current_day + datetime.timedelta(days=offset)

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
