"""Tests for serializers for the Learner Dashboard"""

import datetime
from random import getrandbits, randint
from time import time
from unittest import TestCase
from unittest import mock
from uuid import uuid4

from lms.djangoapps.learner_dashboard.serializers import (
    CourseProviderSerializer,
    CourseRunSerializer,
    CourseSerializer,
    EnrollmentSerializer,
    GradeDataSerializer,
    PlatformSettingsSerializer,
    LearnerDashboardSerializer,
)


def random_bool():
    """Test util for generating a random boolean"""
    return bool(getrandbits(1))


def random_date():
    """Test util for generating a random date"""
    d = randint(1, int(time()))
    return datetime.datetime.fromtimestamp(d)


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


class TestCourseRunSerializer(TestCase):
    """Tests for the CourseRunSerializer"""

    def test_happy_path(self):
        input_data = {
            "isPending": random_bool(),
            "isStarted": random_bool(),
            "isFinished": random_bool(),
            "isArchived": random_bool(),
            "courseNumber": f"{uuid4()}-101",
            "accessExpirationDate": random_date(),
            "minPassingGrade": randint(0, 10000) / 100,
            "endDate": random_date(),
            "homeUrl": f"{uuid4()}.example.com",
            "marketingUrl": f"{uuid4()}.example.com",
            "progressUrl": f"{uuid4()}.example.com",
            "unenrollUrl": f"{uuid4()}.example.com",
            "upgradeUrl": f"{uuid4()}.example.com",
        }
        output_data = CourseRunSerializer(input_data).data

        assert output_data == {
            "isPending": input_data["isPending"],
            "isStarted": input_data["isStarted"],
            "isFinished": input_data["isFinished"],
            "isArchived": input_data["isArchived"],
            "courseNumber": input_data["courseNumber"],
            "accessExpirationDate": input_data["accessExpirationDate"].strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "minPassingGrade": str(input_data["minPassingGrade"]),
            "endDate": input_data["endDate"].strftime("%Y-%m-%dT%H:%M:%SZ"),
            "homeUrl": input_data["homeUrl"],
            "marketingUrl": input_data["marketingUrl"],
            "progressUrl": input_data["progressUrl"],
            "unenrollUrl": input_data["unenrollUrl"],
            "upgradeUrl": input_data["upgradeUrl"],
        }


class TestEnrollmentSerializer(TestCase):
    """Tests for the EnrollmentSerializer"""

    def test_happy_path(self):
        input_data = {
            "isAudit": random_bool(),
            "isVerified": random_bool(),
            "canUpgrade": random_bool(),
            "isAuditAccessExpired": random_bool(),
            "isEmailEnabled": random_bool(),
        }
        output_data = EnrollmentSerializer(input_data).data

        assert output_data == {
            "isAudit": input_data["isAudit"],
            "isVerified": input_data["isVerified"],
            "canUpgrade": input_data["canUpgrade"],
            "isAuditAccessExpired": input_data["isAuditAccessExpired"],
            "isEmailEnabled": input_data["isEmailEnabled"],
        }


class TestGradeDataSerializer(TestCase):
    """Tests for the GradeDataSerializer"""

    def test_happy_path(self):
        input_data = {
            "isPassing": random_bool(),
        }
        output_data = GradeDataSerializer(input_data).data

        assert output_data == {
            "isPassing": input_data["isPassing"],
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
