"""
Tests for download courses API view.
"""

from unittest.mock import patch

from django.urls import reverse
from rest_framework import status

from common.djangoapps.student.tests.factories import CourseEnrollmentFactory
from lms.djangoapps.mobile_api.testutils import MobileAPITestCase
from openedx.features.offline_mode.models import OfflineCourseSize


class DownloadCoursesAPIViewTest(MobileAPITestCase):
    """
    Download courses API view tests.
    """

    def setUp(self):
        super().setUp()
        self.enrollment = CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id, is_active=True)
        self.url = reverse("download-courses", kwargs={"api_version": "v1", "username": self.user.username})
        self.login_and_enroll()

    @patch("lms.djangoapps.mobile_api.download_courses.views.is_mobile_available_for_user", return_value=True)
    def test_get_download_courses_success(self, mock_mobile_available):
        """
        Test that the API returns the expected response.
        """
        OfflineCourseSize.objects.create(course_id=self.course.id, size=123456)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["course_id"], str(self.course.id))
        self.assertEqual(response.data[0]["course_name"], self.course.display_name)
        self.assertEqual(response.data[0]["course_image"], self.enrollment.course_overview.course_image_url)
        self.assertEqual(response.data[0]["total_size"], 123456)

    @patch("lms.djangoapps.mobile_api.download_courses.views.is_mobile_available_for_user", return_value=True)
    def test_excludes_courses_with_no_offline_content(self, mock_mobile_available):
        """
        Test that courses with no offline content are not returned in the API response.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
