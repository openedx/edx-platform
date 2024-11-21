"""
Tests for view that handles course published event.
"""
from unittest.mock import patch

from django.test import TestCase, RequestFactory
from django.test.client import Client
from django.urls import reverse
from edx_toggles.toggles.testutils import override_waffle_flag

from common.djangoapps.student.tests.factories import UserFactory
from openedx.features.offline_mode.views import SudioCoursePublishedEventHandler

from openedx.features.offline_mode.toggles import ENABLE_OFFLINE_MODE


class TestSudioCoursePublishedEventHandler(TestCase):
    """
    Tests for the SudioCoursePublishedEventHandler view.
    """

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.view = SudioCoursePublishedEventHandler.as_view()
        self.url = reverse('offline_mode:handle_course_published')

        self.user_password = 'Password1234'
        self.user = UserFactory.create(password=self.user_password)
        self.staff_user = UserFactory.create(is_staff=True, password=self.user_password)

    def staff_login(self):
        self.client.login(username=self.staff_user.username, password=self.user_password)

    def test_unauthorized(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data, {'detail': 'Authentication credentials were not provided.'})

    def test_not_admin(self):
        self.client.login(username=self.user.username, password=self.user_password)
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data, {'detail': 'You do not have permission to perform this action.'})

    @override_waffle_flag(ENABLE_OFFLINE_MODE, active=True)
    @patch('openedx.features.offline_mode.views.generate_offline_content_for_course.apply_async')
    def test_admin_enabled_waffle_flag(self, mock_generate_offline_content_for_course_task):
        self.staff_login()
        course_id = 'course-v1:edX+DemoX+Demo_Course'
        response = self.client.post(self.url, {'course_id': course_id})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, None)
        mock_generate_offline_content_for_course_task.assert_called_once_with(args=[course_id])

    @override_waffle_flag(ENABLE_OFFLINE_MODE, active=False)
    def test_admin_disabled_waffle_flag(self):
        self.staff_login()
        response = self.client.post(self.url, {'course_id': 'course-v1:edX+DemoX+Demo_Course'})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'error': 'Offline mode is not enabled for this course'})

    @override_waffle_flag(ENABLE_OFFLINE_MODE, active=True)
    def test_admin_enabled_waffle_flag_no_course_id(self):
        self.staff_login()
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'error': 'course_id is required'})

    @override_waffle_flag(ENABLE_OFFLINE_MODE, active=False)
    def test_admin_disabled_waffle_flag_no_course_id(self):
        self.staff_login()
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'error': 'course_id is required'})

    def test_invalid_course_id(self):
        self.staff_login()
        response = self.client.post(self.url, {'course_id': 'invalid_course_id'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'error': 'Invalid course_id'})
