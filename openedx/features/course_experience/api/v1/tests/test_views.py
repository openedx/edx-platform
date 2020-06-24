"""
Tests for reset deadlines endpoint.
"""
import ddt

from django.urls import reverse

from course_modes.models import CourseMode
from lms.djangoapps.course_home_api.tests.utils import BaseCourseHomeTests
from student.models import CourseEnrollment


@ddt.ddt
class ResetCourseDeadlinesViewTests(BaseCourseHomeTests):
    """
    Tests for reset deadlines endpoint.
    """
    @ddt.data(CourseMode.VERIFIED)
    def test_reset_deadlines(self, enrollment_mode):
        CourseEnrollment.enroll(self.user, self.course.id, enrollment_mode)
        # Test correct post body
        response = self.client.post(reverse('course-experience-reset-course-deadlines'), {'course_key': self.course.id})
        self.assertEqual(response.status_code, 200)
        # Test body with incorrect body param
        response = self.client.post(reverse('course-experience-reset-course-deadlines'), {'course': self.course.id})
        self.assertEqual(response.status_code, 400)
        # Test body with additional incorrect body param
        response = self.client.post(
            reverse('course-experience-reset-course-deadlines'), {'course_key': self.course.id, 'invalid': 'value'}
        )
        self.assertEqual(response.status_code, 400)
