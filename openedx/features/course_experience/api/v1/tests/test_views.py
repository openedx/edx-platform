"""
Tests for reset deadlines endpoint.
"""
import ddt

from django.urls import reverse

from common.djangoapps.course_modes.models import CourseMode
from lms.djangoapps.course_home_api.tests.utils import BaseCourseHomeTests
from common.djangoapps.student.models import CourseEnrollment


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

    def test_post_unauthenticated_user(self):
        self.client.logout()
        response = self.client.post(reverse('course-experience-reset-course-deadlines'), {'course_key': self.course.id})
        self.assertEqual(response.status_code, 401)

    def test_mobile_get_banner_info(self):
        response = self.client.get(reverse('course-experience-course-deadlines-mobile', args=[self.course.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'missed_deadlines')
        self.assertContains(response, 'missed_gated_content')
        self.assertContains(response, 'content_type_gating_enabled')
        self.assertContains(response, 'verified_upgrade_link')

    def test_mobile_get_unknown_course(self):
        url = reverse('course-experience-course-deadlines-mobile', args=['course-v1:unknown+course+2T2020'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_mobile_get_unauthenticated_user(self):
        self.client.logout()
        response = self.client.get(reverse('course-experience-course-deadlines-mobile', args=[self.course.id]))
        self.assertEqual(response.status_code, 401)
