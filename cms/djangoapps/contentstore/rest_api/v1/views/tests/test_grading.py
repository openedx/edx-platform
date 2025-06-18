"""
Unit tests for course grading views.
"""
import json
from unittest.mock import patch

import ddt
from django.urls import reverse
from rest_framework import status

from cms.djangoapps.contentstore.tests.utils import CourseTestCase
from cms.djangoapps.contentstore.utils import get_proctored_exam_settings_url
from cms.djangoapps.models.settings.course_grading import CourseGradingModel
from openedx.core.djangoapps.credit.tests.factories import CreditCourseFactory

from ...mixins import PermissionAccessMixin


@ddt.ddt
class CourseGradingViewTest(CourseTestCase, PermissionAccessMixin):
    """
    Tests for CourseGradingView.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "cms.djangoapps.contentstore:v1:course_grading",
            kwargs={"course_id": self.course.id},
        )

    def test_course_grading_response(self):
        """Check successful response content"""
        response = self.client.get(self.url)
        grading_data = CourseGradingModel.fetch(self.course.id)

        expected_response = {
            "mfe_proctored_exam_settings_url": get_proctored_exam_settings_url(
                self.course.id
            ),
            "course_assignment_lists": {},
            "course_details": grading_data.__dict__,
            "show_credit_eligibility": False,
            "is_credit_course": False,
            "default_grade_designations": ['A', 'B', 'C', 'D'],
        }

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(expected_response, response.data)

    @patch("django.conf.settings.DEFAULT_GRADE_DESIGNATIONS", ['A', 'B'])
    def test_default_grade_designations_setting(self):
        """
        Check that DEFAULT_GRADE_DESIGNATIONS setting reflects correctly in API.
        """
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(['A', 'B'], response.data["default_grade_designations"])

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_CREDIT_ELIGIBILITY": True})
    def test_credit_eligibility_setting(self):
        """
        Make sure if the feature flag is enabled we have enabled values in response.
        """
        _ = CreditCourseFactory(course_key=self.course.id, enabled=True)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["show_credit_eligibility"])
        self.assertTrue(response.data["is_credit_course"])

    def test_post_permissions_unauthenticated(self):
        """
        Test that an error is returned in the absence of auth credentials.
        """
        self.client.logout()
        response = self.client.post(self.url)
        error = self.get_and_check_developer_response(response)
        self.assertEqual(error, "Authentication credentials were not provided.")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_permissions_unauthorized(self):
        """
        Test that an error is returned if the user is unauthorised.
        """
        client, _ = self.create_non_staff_authed_user_client()
        response = client.post(self.url)
        error = self.get_and_check_developer_response(response)
        self.assertEqual(error, "You do not have permission to perform this action.")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch(
        "openedx.core.djangoapps.credit.tasks.update_credit_course_requirements.delay"
    )
    def test_post_course_grading(self, mock_update_credit_course_requirements):
        """Check successful request with called task"""
        request_data = {
            "graders": [
                {
                    "type": "Homework",
                    "min_count": 1,
                    "drop_count": 0,
                    "short_label": "",
                    "weight": 100,
                    "id": 0,
                }
            ],
            "grade_cutoffs": {"A": 0.75, "B": 0.63, "C": 0.57, "D": 0.5},
            "grace_period": {"hours": 12, "minutes": 0},
            "minimum_grade_credit": 0.7,
            "is_credit_course": True,
        }
        response = self.client.post(
            path=self.url,
            data=json.dumps(request_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_update_credit_course_requirements.assert_called_once()

    def test_post_course_grading_with_valid_color(self):
        """
        Test POST with valid hex color in grader data
        """
        request_data = {
            "graders": [
                {
                    "type": "Homework",
                    "min_count": 1,
                    "drop_count": 0,
                    "short_label": "",
                    "weight": 100,
                    "id": 0,
                    "color": "#FF5733"
                }
            ],
            "grade_cutoffs": {"A": 0.75, "B": 0.63, "C": 0.57, "D": 0.5},
            "grace_period": {"hours": 12, "minutes": 0},
            "minimum_grade_credit": 0.7,
        }
        response = self.client.post(
            path=self.url,
            data=json.dumps(request_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual("#FF5733", response.data['graders'][0]['color'])

    def test_post_course_grading_with_invalid_color_format(self):
        """
        Test POST with invalid hex color format
        """
        request_data = {
            "graders": [
                {
                    "type": "Homework",
                    "min_count": 1,
                    "drop_count": 0,
                    "short_label": "",
                    "weight": 100,
                    "id": 0,
                    "color": "invalid_color"
                }
            ],
            "grade_cutoffs": {"A": 0.75, "B": 0.63, "C": 0.57, "D": 0.5},
            "grace_period": {"hours": 12, "minutes": 0},
            "minimum_grade_credit": 0.7,
        }
        response = self.client.post(
            path=self.url,
            data=json.dumps(request_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data['developer_message'][0]['color'][0],
            'Invalid color format. Must be a hex color code.'
        )

    def test_post_course_grading_with_short_hex_color(self):
        """
        Test POST with 3-character hex color
        """
        request_data = {
            "graders": [
                {
                    "type": "Homework",
                    "min_count": 1,
                    "drop_count": 0,
                    "short_label": "",
                    "weight": 100,
                    "id": 0,
                    "color": "#F5A"
                }
            ],
            "grade_cutoffs": {"A": 0.75, "B": 0.63, "C": 0.57, "D": 0.5},
            "grace_period": {"hours": 12, "minutes": 0},
            "minimum_grade_credit": 0.7,
        }
        response = self.client.post(
            path=self.url,
            data=json.dumps(request_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['graders'][0]['color'], "#F5A")

    def test_post_course_grading_with_missing_hash_symbol(self):
        """
        Test POST with hex color missing hash symbol
        """
        request_data = {
            "graders": [
                {
                    "type": "Homework",
                    "min_count": 1,
                    "drop_count": 0,
                    "short_label": "",
                    "weight": 100,
                    "id": 0,
                    "color": "FF5733"
                }
            ],
            "grade_cutoffs": {"A": 0.75, "B": 0.63, "C": 0.57, "D": 0.5},
            "grace_period": {"hours": 12, "minutes": 0},
            "minimum_grade_credit": 0.7,
        }
        response = self.client.post(
            path=self.url,
            data=json.dumps(request_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data['developer_message'][0]['color'][0],
            'Invalid color format. Must be a hex color code.'
        )

    def test_post_course_grading_with_multiple_graders_mixed_colors(self):
        """
        Test POST with multiple graders having valid and invalid colors
        """
        request_data = {
            "graders": [
                {
                    "type": "Homework",
                    "min_count": 1,
                    "drop_count": 0,
                    "short_label": "",
                    "weight": 50,
                    "id": 0,
                    "color": "#FF5733"
                },
                {
                    "type": "Exam",
                    "min_count": 1,
                    "drop_count": 0,
                    "short_label": "",
                    "weight": 50,
                    "id": 1,
                    "color": "not_a_color"
                }
            ],
            "grade_cutoffs": {"A": 0.75, "B": 0.63, "C": 0.57, "D": 0.5},
            "grace_period": {"hours": 12, "minutes": 0},
            "minimum_grade_credit": 0.7,
        }
        response = self.client.post(
            path=self.url,
            data=json.dumps(request_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data['developer_message'][1]['color'][0],
            'Invalid color format. Must be a hex color code.'
        )

    def test_post_course_grading_without_color_field(self):
        """
        Test POST with grader data without color field
        """
        request_data = {
            "graders": [
                {
                    "type": "Homework",
                    "min_count": 1,
                    "drop_count": 0,
                    "short_label": "",
                    "weight": 100,
                    "id": 0,
                }
            ],
            "grade_cutoffs": {"A": 0.75, "B": 0.63, "C": 0.57, "D": 0.5},
            "grace_period": {"hours": 12, "minutes": 0},
            "minimum_grade_credit": 0.7,
        }
        response = self.client.post(
            path=self.url,
            data=json.dumps(request_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_course_grading_with_empty_color_field(self):
        """
        Test POST with grader data with empty color field
        """
        request_data = {
            "graders": [
                {
                    "type": "Homework",
                    "min_count": 1,
                    "drop_count": 0,
                    "short_label": "",
                    "weight": 100,
                    "id": 0,
                    "color": ""
                }
            ],
            "grade_cutoffs": {"A": 0.75, "B": 0.63, "C": 0.57, "D": 0.5},
            "grace_period": {"hours": 12, "minutes": 0},
            "minimum_grade_credit": 0.7,
        }
        response = self.client.post(
            path=self.url,
            data=json.dumps(request_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['graders'][0]['color'], "")

    def test_post_get_course_grading_with_color_field(self):
        """
        Test POST and GET with grader data with color field
        """
        request_data = {
            "graders": [
                {
                    "type": "Homework",
                    "min_count": 1,
                    "drop_count": 0,
                    "short_label": "",
                    "weight": 100,
                    "id": 0,
                    "color": "#FF5733"
                }
            ],
            "grade_cutoffs": {"A": 0.75, "B": 0.63, "C": 0.57, "D": 0.5},
            "grace_period": {"hours": 12, "minutes": 0},
            "minimum_grade_credit": 0.7,
        }
        post_response = self.client.post(
            path=self.url,
            data=json.dumps(request_data),
            content_type="application/json",
        )
        self.assertEqual(post_response.status_code, status.HTTP_200_OK)

        get_response = self.client.get(self.url)
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.data['course_details']['graders'][0]['color'], "#FF5733")
