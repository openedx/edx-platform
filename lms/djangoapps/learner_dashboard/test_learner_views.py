"""Test for learner views and related functions"""

import json
from unittest import TestCase
from unittest.mock import patch
from uuid import uuid4

from django.urls import reverse
from rest_framework.test import APITestCase

from lms.djangoapps.learner_dashboard.learner_views import get_platform_settings
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import (
    TEST_DATA_SPLIT_MODULESTORE,
    SharedModuleStoreTestCase,
)
from xmodule.modulestore.tests.factories import CourseFactory


class TestGetPlatformSettings(TestCase):
    """Tests for get_platform_settings"""

    MOCK_SETTINGS = {
        "DEFAULT_FEEDBACK_EMAIL": f"{uuid4()}@example.com",
        "PAYMENT_SUPPORT_EMAIL": f"{uuid4()}@example.com",
    }

    @patch.multiple("django.conf.settings", **MOCK_SETTINGS)
    @patch("lms.djangoapps.learner_dashboard.learner_views.marketing_link")
    def test_happy_path(self, mock_marketing_link):
        # Given email/search info exists
        mock_marketing_link.return_value = mock_search_url = f"/{uuid4()}"

        # When I request those settings
        return_data = get_platform_settings()

        # Then I return them in the appropriate format
        self.assertDictEqual(
            return_data,
            {
                "supportEmail": self.MOCK_SETTINGS["DEFAULT_FEEDBACK_EMAIL"],
                "billingEmail": self.MOCK_SETTINGS["PAYMENT_SUPPORT_EMAIL"],
                "courseSearchUrl": mock_search_url,
            },
        )


class TestDashboardView(SharedModuleStoreTestCase, APITestCase):
    """Tests for the dashboard view"""

    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Get view URL
        cls.view_url = reverse("dashboard_view")

        # Set up a course
        cls.course = CourseFactory.create()
        cls.course_key = cls.course.location.course_key

        # Set up a user
        cls.username = "alan"
        cls.password = "enigma"
        cls.user = UserFactory(username=cls.username, password=cls.password)

    def log_in(self):
        """Log in as a test user"""
        self.client.login(username=self.username, password=self.password)

    def setUp(self):
        super().setUp()
        self.log_in()

    def test_response_structure(self):
        """Basic test for correct response structure"""

        # Given I am logged in
        self.log_in()

        # When I request the dashboard
        response = self.client.get(self.view_url)

        # Then I get the expected success response
        assert response.status_code == 200

        response_data = json.loads(response.content)
        expected_keys = set(
            [
                "platformSettings",
                "enrollments",
                "unfulfilledEntitlements",
                "suggestedCourses",
            ]
        )

        assert expected_keys == response_data.keys()
