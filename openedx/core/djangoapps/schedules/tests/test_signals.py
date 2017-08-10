from datetime import datetime, timedelta

from pytz import utc

from xmodule.modulestore.tests.factories import CourseFactory
from course_modes.models import CourseMode
from course_modes.tests.factories import CourseModeFactory
from courseware.models import CourseScheduleConfiguration
from openedx.core.djangolib.testing.utils import skip_unless_lms
from student.tests.factories import CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from ..models import Schedule


@skip_unless_lms
class CreateScheduleTests(ModuleStoreTestCase):

    def create_course_run(self):
        now = datetime.now(utc)
        course = CourseFactory.create(start=now + timedelta(days=-1))

        CourseModeFactory(course_id=course.id, mode_slug=CourseMode.AUDIT)
        CourseModeFactory(
            course_id=course.id,
            mode_slug=CourseMode.VERIFIED,
            expiration_datetime=now + timedelta(days=30)
        )
        return course

    def test_not_create_schedule(self):
        course = self.create_course_run()
        CourseScheduleConfiguration.objects.create(course_id=course.id, enabled=False)

        enrollment = CourseEnrollmentFactory(course_id=course.id, mode=CourseMode.AUDIT)
        with self.assertRaises(Schedule.DoesNotExist):
            enrollment.schedule

    def test_create_schedule(self):
        course = self.create_course_run()
        CourseScheduleConfiguration.objects.create(course_id=course.id, enabled=True)
        enrollment = CourseEnrollmentFactory(course_id=course.id, mode=CourseMode.AUDIT)
        self.assertIsNotNone(enrollment.schedule)
