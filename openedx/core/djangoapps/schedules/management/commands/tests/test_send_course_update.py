"""
Tests for send_course_update management command.
"""
import ddt
from mock import patch, _is_started
from unittest import skipUnless

from django.conf import settings

from edx_ace.utils.date import serialize
from openedx.core.djangoapps.schedules import resolvers, tasks
from openedx.core.djangoapps.schedules.config import COURSE_UPDATE_WAFFLE_FLAG
from openedx.core.djangoapps.schedules.management.commands import send_course_update as nudge
from openedx.core.djangoapps.schedules.management.commands.tests.send_email_base import (
    ScheduleSendEmailTestMixin,
    ExperienceTest
)
from openedx.core.djangoapps.schedules.management.commands.tests.upsell_base import ScheduleUpsellTestMixin
from openedx.core.djangoapps.schedules.models import ScheduleExperience
from openedx.core.djangolib.testing.utils import skip_unless_lms
from openedx.core.djangoapps.waffle_utils.testutils import override_waffle_flag
from student.tests.factories import CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


@ddt.ddt
@skip_unless_lms
@skipUnless(
    'openedx.core.djangoapps.schedules.apps.SchedulesConfig' in settings.INSTALLED_APPS,
    "Can't test schedules if the app isn't installed",
)
class TestSendCourseUpdate(ScheduleUpsellTestMixin, ScheduleSendEmailTestMixin, ModuleStoreTestCase):
    shard = 6
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
        self.highlights_patcher = patch('openedx.core.djangoapps.schedules.resolvers.get_week_highlights')
        mock_highlights = self.highlights_patcher.start()
        mock_highlights.return_value = ['Highlight {}'.format(num + 1) for num in range(3)]
        self.addCleanup(self.stop_highlights_patcher)

    def stop_highlights_patcher(self):
        """
        Stops the patcher for the get_week_highlights method
        if the patch is still in progress.
        """
        if _is_started(self.highlights_patcher):
            self.highlights_patcher.stop()

    @ddt.data(
        ExperienceTest(experience=ScheduleExperience.EXPERIENCES.default, offset=expected_offsets[0], email_sent=False),
        ExperienceTest(experience=ScheduleExperience.EXPERIENCES.course_updates, offset=expected_offsets[0], email_sent=True),
        ExperienceTest(experience=None, offset=expected_offsets[0], email_sent=False),
    )
    def test_schedule_in_different_experience(self, test_config):
        self._check_if_email_sent_for_experience(test_config)

    @override_waffle_flag(COURSE_UPDATE_WAFFLE_FLAG, True)
    @patch('openedx.core.djangoapps.schedules.signals.get_current_site')
    def test_with_course_data(self, mock_get_current_site):
        self.highlights_patcher.stop()
        mock_get_current_site.return_value = self.site_config.site

        course = CourseFactory(highlights_enabled_for_messaging=True, self_paced=True)
        with self.store.bulk_operations(course.id):
            ItemFactory.create(parent=course, category='chapter', highlights=[u'highlights'])

        enrollment = CourseEnrollmentFactory(course_id=course.id, user=self.user, mode=u'audit')
        self.assertEqual(enrollment.schedule.get_experience_type(), ScheduleExperience.EXPERIENCES.course_updates)

        _, offset, target_day, _ = self._get_dates(offset=self.expected_offsets[0])
        enrollment.schedule.start = target_day
        enrollment.schedule.save()

        with patch.object(tasks, 'ace') as mock_ace:
            self.task().apply(kwargs=dict(
                site_id=self.site_config.site.id,
                target_day_str=serialize(target_day),
                day_offset=offset,
                bin_num=self._calculate_bin_for_user(enrollment.user),
            ))

            self.assertTrue(mock_ace.send.called)
