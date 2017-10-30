from mock import patch
from unittest import skipUnless

from django.conf import settings

from openedx.core.djangoapps.schedules import resolvers, tasks
from openedx.core.djangoapps.schedules.management.commands import send_course_update as nudge
from openedx.core.djangoapps.schedules.management.commands.tests.send_email_base import ScheduleSendEmailTestBase
from openedx.core.djangoapps.schedules.management.commands.tests.upsell_base import ScheduleUpsellTestMixin
from openedx.core.djangolib.testing.utils import skip_unless_lms


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
    expected_offsets = xrange(-7, -77, -7)

    queries_deadline_for_each_course = True

    def setUp(self):
        super(TestSendCourseUpdate, self).setUp()
        patcher = patch('openedx.core.djangoapps.schedules.resolvers.get_week_highlights')
        mock_highlights = patcher.start()
        mock_highlights.return_value = ['Highlight {}'.format(num + 1) for num in range(3)]
        self.addCleanup(patcher.stop)
