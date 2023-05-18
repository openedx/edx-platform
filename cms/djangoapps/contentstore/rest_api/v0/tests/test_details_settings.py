"""
Tests for the course advanced settings API.
"""
import json

import ddt
from django.urls import reverse
from rest_framework import status

from cms.djangoapps.contentstore.tests.utils import CourseTestCase


@ddt.ddt
class CourseDetailsSettingViewTest(CourseTestCase):
    """
    Tests for DetailsSettings API View.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "cms.djangoapps.contentstore:v0:course_details_settings",
            kwargs={"course_id": self.course.id},
        )

    def get_and_check_developer_response(self, response):
        """
        Make basic asserting about the presence of an error response, and return the developer response.
        """
        content = json.loads(response.content.decode("utf-8"))
        assert "developer_message" in content
        return content["developer_message"]

    def test_permissions_unauthenticated(self):
        """
        Test that an error is returned in the absence of auth credentials.
        """
        self.client.logout()
        response = self.client.get(self.url)
        error = self.get_and_check_developer_response(response)
        assert error == "Authentication credentials were not provided."

    def test_permissions_unauthorized(self):
        """
        Test that an error is returned if the user is unauthorised.
        """
        client, _ = self.create_non_staff_authed_user_client()
        response = client.get(self.url)
        error = self.get_and_check_developer_response(response)
        assert error == "You do not have permission to perform this action."

    def test_get_course_details(self):
        """
        Test for get response
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patch_course_details(self):
        """
        Test for patch response
        """
        data = {
            "start_date": "2030-01-01T00:00:00Z",
            "end_date": "2030-01-31T00:00:00Z",
            "enrollment_start": "2029-12-01T00:00:00Z",
            "enrollment_end": "2030-01-01T00:00:00Z",
            "course_title": "Test Course",
            "short_description": "This is a test course",
            "overview": "This course is for testing purposes",
            "intro_video": None
        }
        response = self.client.patch(self.url, data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
