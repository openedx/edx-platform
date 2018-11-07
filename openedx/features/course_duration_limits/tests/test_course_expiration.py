"""
Contains tests to verify correctness of course expiration functionality
"""
from datetime import timedelta
from django.utils.timezone import now
import ddt
import mock


from course_modes.models import CourseMode
from openedx.features.course_duration_limits.access import get_user_course_expiration_date, MIN_DURATION, MAX_DURATION
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@ddt.ddt
class CourseExpirationTestCase(ModuleStoreTestCase):
    """Tests to verify the get_user_course_expiration_date function is working correctly"""
    def setUp(self):
        super(CourseExpirationTestCase, self).setUp()
        self.course = CourseFactory(
            start=now() - timedelta(weeks=10),
        )
        self.user = UserFactory()

    def tearDown(self):
        CourseEnrollment.unenroll(self.user, self.course.id)
        super(CourseExpirationTestCase, self).tearDown()

    def test_enrollment_mode(self):
        """Tests that verified enrollments do not have an expiration"""
        CourseEnrollment.enroll(self.user, self.course.id, CourseMode.VERIFIED)
        result = get_user_course_expiration_date(self.user, self.course)
        self.assertEqual(result, None)

    @mock.patch("openedx.features.course_duration_limits.access.get_course_run_details")
    @ddt.data(
        [int(MIN_DURATION.days / 7) - 1, MIN_DURATION, False],
        [7, timedelta(weeks=7), False],
        [int(MAX_DURATION.days / 7) + 1, MAX_DURATION, False],
        [None, MIN_DURATION, False],
        [int(MIN_DURATION.days / 7) - 1, MIN_DURATION, True],
        [7, timedelta(weeks=7), True],
        [int(MAX_DURATION.days / 7) + 1, MAX_DURATION, True],
        [None, MIN_DURATION, True],
    )
    @ddt.unpack
    def test_all_courses_with_weeks_to_complete(
        self,
        weeks_to_complete,
        access_duration,
        self_paced,
        mock_get_course_run_details,
    ):
        """
        Test that access_duration for a course is equal to the value of the weeks_to_complete field in discovery.
        If weeks_to_complete is None, access_duration will be the MIN_DURATION constant.

        """
        if self_paced:
            self.course.self_paced = True
        mock_get_course_run_details.return_value = {'weeks_to_complete': weeks_to_complete}
        enrollment = CourseEnrollment.enroll(self.user, self.course.id, CourseMode.AUDIT)
        result = get_user_course_expiration_date(self.user, self.course)
        self.assertEqual(result, enrollment.created + access_duration)

    @mock.patch("openedx.features.course_duration_limits.access.get_course_run_details")
    def test_content_availability_date(self, mock_get_course_run_details):
        """
        Content availability date is course start date or enrollment date, whichever is later.
        """
        access_duration = timedelta(weeks=7)
        mock_get_course_run_details.return_value = {'weeks_to_complete': 7}

        # Content availability date is enrollment date
        start_date = now() - timedelta(weeks=10)
        past_course = CourseFactory(start=start_date)
        enrollment = CourseEnrollment.enroll(self.user, past_course.id, CourseMode.AUDIT)
        result = get_user_course_expiration_date(self.user, past_course)
        content_availability_date = enrollment.created
        self.assertEqual(result, content_availability_date + access_duration)

        # Content availability date is course start date
        start_date = now() + timedelta(weeks=10)
        future_course = CourseFactory(start=start_date)
        enrollment = CourseEnrollment.enroll(self.user, future_course.id, CourseMode.AUDIT)
        result = get_user_course_expiration_date(self.user, future_course)
        content_availability_date = start_date
        self.assertEqual(result, content_availability_date + access_duration)
