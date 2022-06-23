"""Tests for Learner Dashboard-related APIs"""

from unittest import TestCase
from unittest.mock import patch
from uuid import uuid4

from lms.djangoapps.learner_dashboard.learner_api import get_platform_settings


class TestGetPlatformSettings(TestCase):
    """Tests for get_platform_settings"""

    MOCK_SETTINGS = {
        "DEFAULT_FEEDBACK_EMAIL": f"{uuid4()}@example.com",
        "PAYMENT_SUPPORT_EMAIL": f"{uuid4()}@example.com",
    }

    @patch.multiple("django.conf.settings", **MOCK_SETTINGS)
    @patch("lms.djangoapps.learner_dashboard.learner_apis.marketing_link")
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
