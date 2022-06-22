"""Tests for serializers for the Learner Dashboard"""

from unittest import TestCase
from unittest import mock
from uuid import uuid4

from lms.djangoapps.learner_dashboard.serializers import (
    EdxSerializer,
    LearnerDashboardSerializer,
)


class TestEdxSerializer(TestCase):
    """Tests for the EdxSerializer"""

    def test_happy_path(self):
        input_data = {
            "feedbackEmail": f"{uuid4()}@example.com",
            "supportEmail": f"{uuid4()}@example.com",
            "billingEmail": f"{uuid4()}@example.com",
            "courseSearchUrl": f"{uuid4()}.example.com/search",
        }
        output_data = EdxSerializer(input_data).data

        assert output_data == {
            "feedbackEmail": input_data["feedbackEmail"],
            "supportEmail": input_data["supportEmail"],
            "billingEmail": input_data["billingEmail"],
            "courseSearchUrl": input_data["courseSearchUrl"],
        }


class TestLearnerDashboardSerializer(TestCase):
    """High-level tests for Learner Dashboard serialization"""

    # Show full diff for serialization issues
    maxDiff = None

    def test_empty(self):
        """Test that empty inputs return the right keys"""

        input_data = {
            "edx": None,
            "enrollments": [],
            "unfulfilledEntitlements": [],
            "suggestedCourses": [],
        }
        output_data = LearnerDashboardSerializer(input_data).data

        self.assertDictEqual(
            output_data,
            {
                "edx": None,
                "enrollments": [],
                "unfulfilledEntitlements": [],
                "suggestedCourses": [],
            },
        )

    def test_linkage(self):
        """Test that serializers link to their appropriate outputs"""
        input_data = {
            "edx": {},
            "enrollments": [],
            "unfulfilledEntitlements": [],
            "suggestedCourses": [],
        }
        serializer = LearnerDashboardSerializer(input_data)
        with mock.patch(
            "lms.djangoapps.learner_dashboard.serializers.EdxSerializer.to_representation"
        ) as mock_edx_serializer:
            mock_edx_serializer.return_value = mock_edx_serializer
            output_data = serializer.data

        self.assertDictEqual(
            output_data,
            {
                "edx": mock_edx_serializer,
                "enrollments": [],
                "unfulfilledEntitlements": [],
                "suggestedCourses": [],
            },
        )

    @mock.patch(
        "lms.djangoapps.learner_dashboard.serializers.EdxSerializer.to_representation"
    )
    def test_linkage2(self, mock_edx_serializer):
        """Second example of paradigm using test-level patching"""
        mock_edx_serializer.return_value = mock_edx_serializer

        input_data = {
            "edx": {},
            "enrollments": [],
            "unfulfilledEntitlements": [],
            "suggestedCourses": [],
        }
        output_data = LearnerDashboardSerializer(input_data).data

        self.assertDictEqual(
            output_data,
            {
                "edx": mock_edx_serializer,
                "enrollments": [],
                "unfulfilledEntitlements": [],
                "suggestedCourses": [],
            },
        )
