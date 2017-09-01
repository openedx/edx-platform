import datetime
from mock import patch
from pytz import utc

from course_modes.models import CourseMode
from course_modes.tests.factories import CourseModeFactory
from courseware.models import DynamicUpgradeDeadlineConfiguration
from openedx.core.djangoapps.schedules.signals import SCHEDULE_WAFFLE_FLAG
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.core.djangoapps.waffle_utils.testutils import override_waffle_flag
from openedx.core.djangolib.testing.utils import skip_unless_lms
from student.tests.factories import CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from ..models import Schedule
from ..tests.factories import ScheduleConfigFactory


@patch('openedx.core.djangoapps.schedules.signals.get_current_site')
@skip_unless_lms
class CreateScheduleTests(SharedModuleStoreTestCase):

    def assert_schedule_created(self):
        enrollment = CourseEnrollmentFactory()
        self.assertIsNotNone(enrollment.schedule)
        self.assertIsNone(enrollment.schedule.upgrade_deadline)

    def assert_schedule_not_created(self):
        enrollment = CourseEnrollmentFactory()
        with self.assertRaises(Schedule.DoesNotExist):
            enrollment.schedule

    @override_waffle_flag(SCHEDULE_WAFFLE_FLAG, True)
    def test_create_schedule(self, mock_get_current_site):
        site = SiteFactory.create()
        mock_get_current_site.return_value = site
        ScheduleConfigFactory.create(site=site)
        self.assert_schedule_created()

    @override_waffle_flag(SCHEDULE_WAFFLE_FLAG, True)
    def test_no_current_site(self, mock_get_current_site):
        mock_get_current_site.return_value = None
        self.assert_schedule_not_created()

    @override_waffle_flag(SCHEDULE_WAFFLE_FLAG, True)
    def test_schedule_config_disabled_waffle_enabled(self, mock_get_current_site):
        site = SiteFactory.create()
        mock_get_current_site.return_value = site
        ScheduleConfigFactory.create(site=site, create_schedules=False)
        self.assert_schedule_created()

    @override_waffle_flag(SCHEDULE_WAFFLE_FLAG, False)
    def test_schedule_config_enabled_waffle_disabled(self, mock_get_current_site):
        site = SiteFactory.create()
        mock_get_current_site.return_value = site
        ScheduleConfigFactory.create(site=site, create_schedules=True)
        self.assert_schedule_created()

    @override_waffle_flag(SCHEDULE_WAFFLE_FLAG, False)
    def test_schedule_config_disabled_waffle_disabled(self, mock_get_current_site):
        site = SiteFactory.create()
        mock_get_current_site.return_value = site
        ScheduleConfigFactory.create(site=site, create_schedules=False)
        self.assert_schedule_not_created()

    @override_waffle_flag(SCHEDULE_WAFFLE_FLAG, True)
    def test_schedule_config_creation_enabled_instructor_paced(self, mock_get_current_site):
        site = SiteFactory.create()
        mock_get_current_site.return_value = site
        ScheduleConfigFactory.create(site=site, enabled=True, create_schedules=True)
        course = create_self_paced_course_run()
        DynamicUpgradeDeadlineConfiguration.objects.create(enabled=False)
        enrollment = CourseEnrollmentFactory(course_id=course.id, mode=CourseMode.AUDIT)

        self.assertEqual(enrollment.schedule.start, enrollment.created)
        self.assertIsNone(enrollment.schedule.upgrade_deadline)

    @override_waffle_flag(SCHEDULE_WAFFLE_FLAG, True)
    def test_schedule_config_creation_enabled_instructor_paced_with_deadline(self, mock_get_current_site):
        site = SiteFactory.create()
        mock_get_current_site.return_value = site
        ScheduleConfigFactory.create(site=site, enabled=True, create_schedules=True)
        course = create_self_paced_course_run()
        global_config = DynamicUpgradeDeadlineConfiguration.objects.create(enabled=True)
        enrollment = CourseEnrollmentFactory(course_id=course.id, mode=CourseMode.AUDIT)
        expected_deadline = enrollment.created + datetime.timedelta(days=global_config.deadline_days)

        self.assertEqual(enrollment.schedule.start, enrollment.created)
        self.assertEqual(enrollment.schedule.upgrade_deadline, expected_deadline)


def create_self_paced_course_run():
    """ Create a new course run and course modes.

    Both audit and verified `CourseMode` objects will be created for the course run.
    """
    now = datetime.datetime.now(utc)
    course = CourseFactory.create(start=now + datetime.timedelta(days=-1), self_paced=True)

    CourseModeFactory(
        course_id=course.id,
        mode_slug=CourseMode.AUDIT
    )
    CourseModeFactory(
        course_id=course.id,
        mode_slug=CourseMode.VERIFIED,
        expiration_datetime=now + datetime.timedelta(days=100)
    )

    return course
