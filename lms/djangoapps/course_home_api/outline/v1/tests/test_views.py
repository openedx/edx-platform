"""
Tests for Outline Tab API in the Course Home API
"""


import ddt

from django.urls import reverse

from course_modes.models import CourseMode
from lms.djangoapps.course_home_api.tests.utils import BaseCourseHomeTests
from student.models import CourseEnrollment


@ddt.ddt
class OutlineTabTestViews(BaseCourseHomeTests):
    """
    Tests for the Outline Tab API
    """
    @classmethod
    def setUpClass(cls):
        BaseCourseHomeTests.setUpClass()
        cls.url = reverse('course-home-outline-tab', args=[cls.course.id])

    @ddt.data(CourseMode.AUDIT, CourseMode.VERIFIED)
    def test_get_authenticated_enrolled_user(self, enrollment_mode):
        CourseEnrollment.enroll(self.user, self.course.id, enrollment_mode)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        course_tools = response.data.get('course_tools')
        self.assertTrue(course_tools)
        self.assertEquals(course_tools[0]['analytics_id'], 'edx.bookmarks')

    def test_get_authenticated_user_not_enrolled(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data.get('learner_is_verified'))

        course_tools = response.data.get('course_tools')
        self.assertEqual(len(course_tools), 0)

    def test_get_unauthenticated_user(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    # TODO: write test_get_unknown_course when more data is pulled into the Outline Tab API
