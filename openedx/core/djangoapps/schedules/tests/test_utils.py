"""
Tests for schedules utils
"""

import datetime

import ddt
from pytz import utc

from common.djangoapps.course_modes.models import CourseMode
from openedx.core.djangoapps.schedules.models import Schedule
from openedx.core.djangoapps.schedules.tests.factories import ScheduleConfigFactory
from openedx.core.djangoapps.schedules.utils import reset_self_paced_schedule
from openedx.core.djangolib.testing.utils import skip_unless_lms
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.tests.factories import CourseFactory  # lint-amnesty, pylint: disable=wrong-import-order


@ddt.ddt
@skip_unless_lms
class ResetSelfPacedScheduleTests(SharedModuleStoreTestCase):  # lint-amnesty, pylint: disable=missing-class-docstring
    def create_schedule(self, offset=0):  # lint-amnesty, pylint: disable=missing-function-docstring
        self.config = ScheduleConfigFactory()  # lint-amnesty, pylint: disable=attribute-defined-outside-init

        start = datetime.datetime.now(utc) - datetime.timedelta(days=100)
        self.course = CourseFactory.create(start=start, self_paced=True)  # lint-amnesty, pylint: disable=attribute-defined-outside-init

        self.enrollment = CourseEnrollmentFactory(  # lint-amnesty, pylint: disable=attribute-defined-outside-init
            course_id=self.course.id,
            mode=CourseMode.AUDIT,
        )
        self.enrollment.created = start + datetime.timedelta(days=offset)
        self.enrollment.save()

        self.schedule = self.enrollment.schedule  # lint-amnesty, pylint: disable=attribute-defined-outside-init
        self.schedule.start_date = self.enrollment.created
        self.schedule.save()

        self.user = self.enrollment.user  # lint-amnesty, pylint: disable=attribute-defined-outside-init

    def test_reset_to_now(self):
        self.create_schedule()
        original_start = self.schedule.start_date

        with self.assertNumQueries(3):
            reset_self_paced_schedule(self.user, self.course.id, use_availability_date=False)

        self.schedule.refresh_from_db()
        assert self.schedule.start_date > original_start

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
        assert self.schedule.start_date.replace(microsecond=0) == expected_start.replace(microsecond=0)

    def test_safe_without_schedule(self):
        """ Just ensure that we don't raise exceptions or create any schedules """
        self.create_schedule()
        self.schedule.delete()

        reset_self_paced_schedule(self.user, self.course.id, use_availability_date=False)
        reset_self_paced_schedule(self.user, self.course.id, use_availability_date=True)

        assert Schedule.objects.count() == 0
