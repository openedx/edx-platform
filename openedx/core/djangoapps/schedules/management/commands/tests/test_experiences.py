from collections import namedtuple

import datetime
import ddt
import pytz
from edx_ace.utils.date import serialize
from freezegun import freeze_time
from mock import patch

from courseware.models import DynamicUpgradeDeadlineConfiguration
from openedx.core.djangoapps.schedules import tasks
from openedx.core.djangoapps.schedules.models import ScheduleExperience
from openedx.core.djangoapps.schedules.resolvers import _get_datetime_beginning_of_day
from openedx.core.djangoapps.schedules.tests.factories import ScheduleFactory, ScheduleConfigFactory
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory, SiteConfigurationFactory
from openedx.core.djangolib.testing.utils import skip_unless_lms, FilteredQueryCountMixin, CacheIsolationTestCase


@ddt.ddt
@skip_unless_lms
@freeze_time('2017-08-01 00:00:00', tz_offset=0, tick=True)
class TestExperiences(FilteredQueryCountMixin, CacheIsolationTestCase):

    ENABLED_CACHES = ['default']

    ExperienceTest = namedtuple('ExperienceTest', 'experience offset email_sent')

    def setUp(self):
        super(TestExperiences, self).setUp()

        site = SiteFactory.create()
        self.site_config = SiteConfigurationFactory.create(site=site)
        ScheduleConfigFactory.create(site=self.site_config.site)

        DynamicUpgradeDeadlineConfiguration.objects.create(enabled=True)

    @ddt.data(
        ExperienceTest(experience=ScheduleExperience.DEFAULT, offset=-3, email_sent=True),
        ExperienceTest(experience=ScheduleExperience.DEFAULT, offset=-10, email_sent=True),
        ExperienceTest(experience=ScheduleExperience.COURSE_UPDATES, offset=-3, email_sent=True),
        ExperienceTest(experience=ScheduleExperience.COURSE_UPDATES, offset=-10, email_sent=False),
    )
    @patch.object(tasks, 'ace')
    def test_experience_type_exclusion(self, test_config, mock_ace):
        current_day = _get_datetime_beginning_of_day(datetime.datetime.now(pytz.UTC))
        target_day = current_day + datetime.timedelta(days=test_config.offset)

        schedule = ScheduleFactory.create(
            start=target_day,
            enrollment__course__self_paced=True,
            experience__experience_type=test_config.experience,
        )

        tasks.ScheduleRecurringNudge.apply(kwargs=dict(
            site_id=self.site_config.site.id, target_day_str=serialize(target_day), day_offset=test_config.offset,
            bin_num=(schedule.enrollment.user.id % tasks.ScheduleRecurringNudge.num_bins),
        ))

        self.assertEqual(mock_ace.send.called, test_config.email_sent)
