"""
Tests for Outline Tab API in the Course Home API
"""

import ddt
from django.urls import reverse

from course_modes.models import CourseMode
from lms.djangoapps.course_home_api.tests.utils import BaseCourseHomeTests
from openedx.core.djangoapps.user_api.preferences.api import set_user_preference
from student.models import CourseEnrollment
from student.tests.factories import UserFactory


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
        self.assertEqual(course_tools[0]['analytics_id'], 'edx.bookmarks')

        dates_widget = response.data.get('dates_widget')
        self.assertTrue(dates_widget)
        date_blocks = dates_widget.get('course_date_blocks')
        self.assertTrue(all((block.get('title') != "") for block in date_blocks))
        self.assertTrue(all(block.get('date') for block in date_blocks))

    def test_get_authenticated_user_not_enrolled(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        course_tools = response.data.get('course_tools')
        self.assertEqual(len(course_tools), 0)

        dates_widget = response.data.get('dates_widget')
        self.assertTrue(dates_widget)
        date_blocks = dates_widget.get('course_date_blocks')
        self.assertTrue(all((block.get('title') != "") for block in date_blocks))
        self.assertTrue(all(block.get('date') for block in date_blocks))

    def test_get_unauthenticated_user(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_masquerade(self):
        user = UserFactory()
        set_user_preference(user, 'time_zone', 'Asia/Tokyo')
        CourseEnrollment.enroll(user, self.course.id)

        self.upgrade_to_staff()  # needed for masquerade

        # Sanity check on our normal user
        self.assertEqual(self.client.get(self.url).data['dates_widget']['user_timezone'], None)

        # Now switch users and confirm we get a different result
        self.update_masquerade(username=user.username)
        self.assertEqual(self.client.get(self.url).data['dates_widget']['user_timezone'], 'Asia/Tokyo')

    # TODO: write test_get_unknown_course when more data is pulled into the Outline Tab API
