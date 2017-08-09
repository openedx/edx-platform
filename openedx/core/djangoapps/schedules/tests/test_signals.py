from django.test import TestCase

from openedx.core.djangoapps.waffle_utils import WaffleSwitchNamespace
from openedx.core.djangolib.testing.utils import skip_unless_lms
from student.tests.factories import CourseEnrollmentFactory
from ..models import Schedule


@skip_unless_lms
class CreateScheduleTests(TestCase):
    def test_create_schedule(self):
        """ A schedule should be created for every new enrollment if the switch is active. """

        SWITCH_NAME = 'enable-create-schedule-receiver'
        switch_namesapce = WaffleSwitchNamespace('schedules')

        with switch_namesapce.override(SWITCH_NAME, True):
            enrollment = CourseEnrollmentFactory()
            self.assertIsNotNone(enrollment.schedule)

        with switch_namesapce.override(SWITCH_NAME, False):
            enrollment = CourseEnrollmentFactory()
            with self.assertRaises(Schedule.DoesNotExist):
                enrollment.schedule
