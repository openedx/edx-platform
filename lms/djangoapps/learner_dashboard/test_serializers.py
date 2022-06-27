"""Tests for serializers for the Learner Dashboard"""

from unittest import TestCase
from unittest import mock
from uuid import uuid4

from lms.djangoapps.learner_dashboard.serializers import (
    CourseProviderSerializer,
    CourseSerializer,
    PlatformSettingsSerializer,
    LearnerDashboardSerializer,
)


class TestPlatformSettingsSerializer(TestCase):
    """Tests for the PlatformSettingsSerializer"""

    def test_happy_path(self):
        input_data = {
            "feedbackEmail": f"{uuid4()}@example.com",
            "supportEmail": f"{uuid4()}@example.com",
            "billingEmail": f"{uuid4()}@example.com",
            "courseSearchUrl": f"{uuid4()}.example.com/search",
        }
        output_data = PlatformSettingsSerializer(input_data).data

        assert output_data == {
            "feedbackEmail": input_data["feedbackEmail"],
            "supportEmail": input_data["supportEmail"],
            "billingEmail": input_data["billingEmail"],
            "courseSearchUrl": input_data["courseSearchUrl"],
        }


class TestCourseProviderSerializer(TestCase):
    """Tests for the CourseProviderSerializer"""

    def test_happy_path(self):
        input_data = {
            "name": f"{uuid4()}",
            "website": f"{uuid4()}.example.com",
            "email": f"{uuid4()}@example.com",
        }
        output_data = CourseProviderSerializer(input_data).data

        assert output_data == {
            "name": input_data["name"],
            "website": input_data["website"],
            "email": input_data["email"],
        }


class TestCourseSerializer(TestCase):
    """Tests for the CourseSerializer"""

    def test_happy_path(self):
        input_data = {
            "bannerImgSrc": f"example.com/assets/{uuid4()}",
            "courseName": f"{uuid4()}",
        }
        output_data = CourseSerializer(input_data).data

        assert output_data == {
            "bannerImgSrc": input_data["bannerImgSrc"],
            "courseName": input_data["courseName"],
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
            "lms.djangoapps.learner_dashboard.serializers.PlatformSettingsSerializer.to_representation"
        ) as mock_platform_settings_serializer:
            mock_platform_settings_serializer.return_value = (
                mock_platform_settings_serializer
            )
            output_data = serializer.data

        self.assertDictEqual(
            output_data,
            {
                "edx": mock_platform_settings_serializer,
                "enrollments": [],
                "unfulfilledEntitlements": [],
                "suggestedCourses": [],
            },
        )

    @mock.patch(
        "lms.djangoapps.learner_dashboard.serializers.PlatformSettingsSerializer.to_representation"
    )
    def test_linkage2(self, mock_platform_settings_serializer):
        """Second example of paradigm using test-level patching"""
        mock_platform_settings_serializer.return_value = (
            mock_platform_settings_serializer
        )

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
                "edx": mock_platform_settings_serializer,
                "enrollments": [],
                "unfulfilledEntitlements": [],
                "suggestedCourses": [],
            },
        )
