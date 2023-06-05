"""
Tests for schedules utils
"""

import datetime

import ddt
from common.djangoapps.course_modes.models import CourseMode
from mock import patch
from pytz import utc

from openedx.core.djangoapps.schedules.models import Schedule
from openedx.core.djangoapps.schedules.tests.factories import ScheduleConfigFactory
from openedx.core.djangoapps.schedules.utils import reset_self_paced_schedule
from openedx.core.djangolib.testing.utils import skip_unless_lms
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@ddt.ddt
@skip_unless_lms
class ResetSelfPacedScheduleTests(SharedModuleStoreTestCase):
    def create_schedule(self, offset=0):
        self.config = ScheduleConfigFactory(create_schedules=True)

        site_patch = patch('openedx.core.djangoapps.schedules.signals.get_current_site', return_value=self.config.site)
        self.addCleanup(site_patch.stop)
        site_patch.start()

        start = datetime.datetime.now(utc) - datetime.timedelta(days=100)
        self.course = CourseFactory.create(start=start, self_paced=True)

        self.enrollment = CourseEnrollmentFactory(
            course_id=self.course.id,
            mode=CourseMode.AUDIT,
        )
        self.enrollment.created = start + datetime.timedelta(days=offset)
        self.enrollment.save()

        self.schedule = self.enrollment.schedule
        self.schedule.start_date = self.enrollment.created
        self.schedule.save()

        self.user = self.enrollment.user

    def test_reset_to_now(self):
        self.create_schedule()
        original_start = self.schedule.start_date

        with self.assertNumQueries(3):
            reset_self_paced_schedule(self.user, self.course.id, use_availability_date=False)

        self.schedule.refresh_from_db()
        self.assertGreater(self.schedule.start_date, original_start)

    @ddt.data(
        (-1, 0),  # enrolled before course started (will reset to start date)
        (1, 1),   # enrolled after course started (will reset to enroll date)
    )
    @ddt.unpack
    def test_reset_to_start_date(self, offset, expected_offset):
        self.create_schedule(offset=offset)
        expected_start = self.course.start + datetime.timedelta(days=expected_offset)

        with self.assertNumQueries(3):
            reset_self_paced_schedule(self.user, self.course.id, use_availability_date=True)

        self.schedule.refresh_from_db()
        self.assertEqual(self.schedule.start_date.replace(microsecond=0), expected_start.replace(microsecond=0))

    def test_safe_without_schedule(self):
        """ Just ensure that we don't raise exceptions or create any schedules """
        self.create_schedule()
        self.schedule.delete()

        reset_self_paced_schedule(self.user, self.course.id, use_availability_date=False)
        reset_self_paced_schedule(self.user, self.course.id, use_availability_date=True)

        self.assertEqual(Schedule.objects.count(), 0)
