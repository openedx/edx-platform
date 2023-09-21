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
        }

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(expected_response, response.data)

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
