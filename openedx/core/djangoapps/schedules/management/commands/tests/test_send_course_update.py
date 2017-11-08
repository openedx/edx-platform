import ddt
from mock import patch
from unittest import skipUnless

from django.conf import settings

from openedx.core.djangoapps.schedules import resolvers, tasks
from openedx.core.djangoapps.schedules.management.commands import send_course_update as nudge
from openedx.core.djangoapps.schedules.management.commands.tests.send_email_base import (
    ScheduleSendEmailTestBase,
    ExperienceTest
)
from openedx.core.djangoapps.schedules.management.commands.tests.upsell_base import ScheduleUpsellTestMixin
from openedx.core.djangoapps.schedules.models import ScheduleExperience
from openedx.core.djangolib.testing.utils import skip_unless_lms


@ddt.ddt
@skip_unless_lms
@skipUnless(
    'openedx.core.djangoapps.schedules.apps.SchedulesConfig' in settings.INSTALLED_APPS,
    "Can't test schedules if the app isn't installed",
)
class TestSendCourseUpdate(ScheduleUpsellTestMixin, ScheduleSendEmailTestBase):
    __test__ = True

    # pylint: disable=protected-access
    resolver = resolvers.CourseUpdateResolver
    task = tasks.ScheduleCourseUpdate
    deliver_task = tasks._course_update_schedule_send
    command = nudge.Command
    deliver_config = 'deliver_course_update'
    enqueue_config = 'enqueue_course_update'
    expected_offsets = range(-7, -77, -7)
    experience_type = ScheduleExperience.EXPERIENCES.course_updates

    queries_deadline_for_each_course = True

    def setUp(self):
        super(TestSendCourseUpdate, self).setUp()
        patcher = patch('openedx.core.djangoapps.schedules.resolvers.get_week_highlights')
        mock_highlights = patcher.start()
        mock_highlights.return_value = ['Highlight {}'.format(num + 1) for num in range(3)]
        self.addCleanup(patcher.stop)

    @ddt.data(
        ExperienceTest(experience=ScheduleExperience.EXPERIENCES.default, offset=expected_offsets[0], email_sent=False),
        ExperienceTest(experience=ScheduleExperience.EXPERIENCES.course_updates, offset=expected_offsets[0], email_sent=True),
        ExperienceTest(experience=None, offset=expected_offsets[0], email_sent=False),
    )
    def test_schedule_in_different_experience(self, test_config):
        self._check_if_email_sent_for_experience(test_config)
