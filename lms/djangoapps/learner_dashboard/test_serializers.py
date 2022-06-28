"""Tests for serializers for the Learner Dashboard"""

import datetime
from random import choice, getrandbits, randint, random
from time import time
from unittest import TestCase
from unittest import mock
from uuid import uuid4

from lms.djangoapps.learner_dashboard.serializers import (
    CertificateSerializer,
    CourseProviderSerializer,
    CourseRunSerializer,
    CourseSerializer,
    EnrollmentSerializer,
    EntitlementSerializer,
    GradeDataSerializer,
    PlatformSettingsSerializer,
    ProgramsSerializer,
    LearnerDashboardSerializer,
)


def random_bool():
    """Test util for generating a random boolean"""
    return bool(getrandbits(1))


def random_date(allow_null=False):
    """Test util for generating a random date, optionally blank"""

    # If null allowed, return null half the time
    if allow_null and random_bool():
        return None

    d = randint(1, int(time()))
    return datetime.datetime.fromtimestamp(d)


def random_url(allow_null=False):
    """Test util for generating a random URL, optionally blank"""

    # If null allowed, return null half the time
    if allow_null and random_bool():
        return None

    random_uuid = uuid4()
    return choice([f"{random_uuid}.example.com", f"example.com/{random_uuid}"])


def datetime_to_django_format(datetime_obj):
    """Util for matching serialized Django datetime format for comparison"""
    if datetime_obj:
        return datetime_obj.strftime("%Y-%m-%dT%H:%M:%SZ")


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
            "accessExpirationDate": datetime_to_django_format(
                input_data["accessExpirationDate"]
            ),
            "minPassingGrade": str(input_data["minPassingGrade"]),
            "endDate": datetime_to_django_format(input_data["endDate"]),
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


class TestCertificateSerializer(TestCase):
    """Tests for the CertificateSerializer"""

    def test_happy_path(self):
        input_data = {
            "availableDate": random_date(allow_null=True),
            "isRestricted": random_bool(),
            "isAvailable": random_bool(),
            "isEarned": random_bool(),
            "isDownloadable": random_bool(),
            "certPreviewUrl": random_url(allow_null=True),
            "certDownloadUrl": random_url(allow_null=True),
            "honorCertDownloadUrl": random_url(allow_null=True),
        }
        output_data = CertificateSerializer(input_data).data

        assert output_data == {
            "availableDate": datetime_to_django_format(input_data["availableDate"]),
            "isRestricted": input_data["isRestricted"],
            "isAvailable": input_data["isAvailable"],
            "isEarned": input_data["isEarned"],
            "isDownloadable": input_data["isDownloadable"],
            "certPreviewUrl": input_data["certPreviewUrl"],
            "certDownloadUrl": input_data["certDownloadUrl"],
            "honorCertDownloadUrl": input_data["honorCertDownloadUrl"],
        }


class TestEntitlementSerializer(TestCase):
    """Tests for the EntitlementSerializer"""

    @classmethod
    def generate_test_session(cls):
        """Generate an test session with random dates and course run numbers"""
        return {
            "startDate": random_date(),
            "endDate": random_date(),
            "courseNumber": f"{uuid4()}-101",
        }

    def test_happy_path(self):
        input_data = {
            "availableSessions": [
                self.generate_test_session() for _ in range(randint(0, 3))
            ],
            "isRefundable": random_bool(),
            "isFulfilled": random_bool(),
            "canViewCourse": random_bool(),
            "changeDeadline": random_date(),
            "isExpired": random_bool(),
        }
        output_data = EntitlementSerializer(input_data).data

        # Compare output sessions separately, since they're more complicated
        output_sessions = output_data.pop("availableSessions")
        for i, output_session in enumerate(output_sessions):
            input_session = input_data["availableSessions"][i]
            input_session["startDate"] = datetime_to_django_format(
                input_session["startDate"]
            )
            input_session["endDate"] = datetime_to_django_format(
                input_session["endDate"]
            )
            assert output_session == input_session

        assert output_data == {
            "isRefundable": input_data["isRefundable"],
            "isFulfilled": input_data["isFulfilled"],
            "canViewCourse": input_data["canViewCourse"],
            "changeDeadline": datetime_to_django_format(input_data["changeDeadline"]),
            "isExpired": input_data["isExpired"],
        }


class TestProgramsSerializer(TestCase):
    """Tests for the ProgramsSerializer and RelatedProgramsSerializer"""

    @classmethod
    def generate_test_related_program(cls):
        """Generate a program with random test data"""
        return {
            "provider": f"{uuid4()} Inc.",
            "programUrl": random_url(),
            "bannerUrl": random_url(),
            "logoUrl": random_url(),
            "title": f"{uuid4()}",
            "programType": f"{uuid4()}",
            "programTypeUrl": random_url(),
            "numberOfCourses": randint(0, 100),
            "estimatedNumberOfWeeks": randint(0, 45),
        }

    def test_happy_path(self):
        input_data = {
            "relatedPrograms": [
                self.generate_test_related_program() for _ in range(randint(0, 3))
            ],
        }
        output_data = ProgramsSerializer(input_data).data

        related_programs = output_data.pop("relatedPrograms")

        for i, related_program in enumerate(related_programs):
            input_program = input_data["relatedPrograms"][i]
            assert related_program == {
                "provider": input_program["provider"],
                "programUrl": input_program["programUrl"],
                "bannerUrl": input_program["bannerUrl"],
                "logoUrl": input_program["logoUrl"],
                "title": input_program["title"],
                "programType": input_program["programType"],
                "programTypeUrl": input_program["programTypeUrl"],
                "numberOfCourses": input_program["numberOfCourses"],
                "estimatedNumberOfWeeks": input_program["estimatedNumberOfWeeks"],
            }

        assert output_data == {}

    def test_empty_sessions(self):
        input_data = {"relatedPrograms": []}
        output_data = ProgramsSerializer(input_data).data

        assert output_data == {"relatedPrograms": []}


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
