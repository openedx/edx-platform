"""Tests for serializers for the Learner Dashboard"""

import datetime
from random import choice, getrandbits, randint
from time import time
from unittest import TestCase
from unittest import mock
from uuid import uuid4
from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.course_modes.tests.factories import CourseModeFactory
from common.djangoapps.student.tests.factories import (
    CourseEnrollmentFactory,
    UserFactory,
)

from lms.djangoapps.learner_dashboard.serializers import (
    CertificateSerializer,
    CourseProviderSerializer,
    CourseRunSerializer,
    CourseSerializer,
    EmailConfirmationSerializer,
    EnrollmentSerializer,
    EnterpriseDashboardsSerializer,
    EntitlementSerializer,
    GradeDataSerializer,
    LearnerEnrollmentSerializer,
    PlatformSettingsSerializer,
    ProgramsSerializer,
    LearnerDashboardSerializer,
    SuggestedCourseSerializer,
    UnfulfilledEntitlementSerializer,
)
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


def random_bool():
    """Test util for generating a random boolean"""
    return bool(getrandbits(1))


def random_date(allow_null=False):
    """Test util for generating a random date, optionally blank"""

    # If null allowed, return null half the time
    if allow_null and random_bool():
        return None

    d = randint(1, int(time()))
    return datetime.datetime.fromtimestamp(d, tz=datetime.timezone.utc)


def random_url(allow_null=False):
    """Test util for generating a random URL, optionally blank"""

    # If null allowed, return null half the time
    if allow_null and random_bool():
        return None

    random_uuid = uuid4()
    return choice([f"{random_uuid}.example.com", f"example.com/{random_uuid}"])


def random_grade():
    """Return a random grade (0-100) with 2 decimal places of padding"""
    return randint(0, 10000) / 100


def decimal_to_grade_format(decimal):
    """Util for matching serialized grade format, pads a decimal to 2 places"""
    return "{:.2f}".format(decimal)


def datetime_to_django_format(datetime_obj):
    """Util for matching serialized Django datetime format for comparison"""
    if datetime_obj:
        return datetime_obj.strftime("%Y-%m-%dT%H:%M:%SZ")


class LearnerDashboardBaseTest(SharedModuleStoreTestCase):
    """Base class for common setup"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory()

    def create_test_enrollment(self):
        course = CourseFactory(self_paced=True)
        CourseModeFactory(
            course_id=course.id,
            mode_slug=CourseMode.AUDIT,
        )

        test_enrollment = CourseEnrollmentFactory(
            course_id=course.id, mode=CourseMode.AUDIT
        )

        # Add extra info to exercise serialization
        test_enrollment.course_overview.marketing_url = random_url()
        test_enrollment.course_overview.end = random_date()

        return test_enrollment


class TestPlatformSettingsSerializer(TestCase):
    """Tests for the PlatformSettingsSerializer"""

    @classmethod
    def generate_test_platform_settings(cls):
        """Util to generate test platform settings data"""
        return {
            "feedbackEmail": f"{uuid4()}@example.com",
            "supportEmail": f"{uuid4()}@example.com",
            "billingEmail": f"{uuid4()}@example.com",
            "courseSearchUrl": f"{uuid4()}.example.com/search",
        }

    def test_happy_path(self):
        input_data = self.generate_test_platform_settings()
        output_data = PlatformSettingsSerializer(input_data).data

        assert output_data == {
            "supportEmail": input_data["supportEmail"],
            "billingEmail": input_data["billingEmail"],
            "courseSearchUrl": input_data["courseSearchUrl"],
        }


class TestCourseProviderSerializer(TestCase):
    """Tests for the CourseProviderSerializer"""

    @classmethod
    def generate_test_provider_info(cls):
        """Util to generate test provider info"""
        return {
            "name": f"{uuid4()}",
        }

    def test_happy_path(self):
        input_data = self.generate_test_provider_info()
        output_data = CourseProviderSerializer(input_data).data

        assert output_data == {
            "name": input_data["name"],
        }


class TestCourseSerializer(LearnerDashboardBaseTest):
    """Tests for the CourseSerializer"""

    def test_happy_path(self):
        test_enrollment = self.create_test_enrollment()

        input_data = test_enrollment.course_overview
        output_data = CourseSerializer(input_data).data

        assert output_data == {
            "bannerImgSrc": test_enrollment.course_overview.banner_image_url,
            "courseName": test_enrollment.course_overview.display_name_with_default,
            "courseNumber": test_enrollment.course_overview.display_number_with_default,
        }


class TestCourseRunSerializer(LearnerDashboardBaseTest):
    """Tests for the CourseRunSerializer"""

    def test_with_data(self):
        input_data = self.create_test_enrollment()

        input_context = {
            "resume_course_urls": {input_data.course.id: random_url()},
            "ecommerce_payment_page": random_url(),
            "course_mode_info": {
                input_data.course.id: {
                    "verified_sku": str(uuid4()),
                    "days_for_upsell": randint(0, 14),
                }
            },
        }

        serializer = CourseRunSerializer(input_data, context=input_context)
        output = serializer.data

        # Serializaiton set up so all fields will have values to make testing easy
        for key in output:
            assert output[key] is not None


class TestEnrollmentSerializer(LearnerDashboardBaseTest):
    """Tests for the EnrollmentSerializer"""

    def create_test_context(self, course):
        """Get a test context object"""
        return {
            "course_mode_info": {
                course.id: {
                    "expiration_datetime": random_date(),
                    "show_upsell": True,
                }
            },
            "course_optouts": [],
            "use_ecommerce_payment_flow": True,
            "show_email_settings_for": [course.id],
            "show_courseware_link": {course.id: {"has_access": True}},
        }

    def test_with_data(self):
        input_data = self.create_test_enrollment()
        input_context = self.create_test_context(input_data.course)

        serializer = EnrollmentSerializer(input_data, context=input_context)
        output = serializer.data

        # Serializaiton set up so all fields will have values to make testing easy
        for key in output:
            assert output[key] is not None

    def test_audit_access_expired(self):
        input_data = self.create_test_enrollment()
        input_context = self.create_test_context(input_data.course)

        # Example audit expired context
        input_context.update(
            {
                "show_courseware_link": {
                    input_data.course.id: {"error_code": "audit_expired"}
                },
            }
        )

        serializer = EnrollmentSerializer(input_data, context=input_context)
        output = serializer.data

        assert output["isAuditAccessExpired"] == True

    def test_user_can_upgrade(self):
        input_data = self.create_test_enrollment()
        input_context = self.create_test_context(input_data.course)

        # Example audit expired context
        input_context.update(
            {
                "course_mode_info": {
                    input_data.course.id: {"show_upsell": True, "verified_sku": uuid4()}
                }
            }
        )

        output = EnrollmentSerializer(input_data, context=input_context).data
        assert output["canUpgrade"] == True


class TestGradeDataSerializer(TestCase):
    """Tests for the GradeDataSerializer"""

    @classmethod
    def generate_test_grade_data(cls):
        """Util to generate test grade data"""
        return {
            "isPassing": random_bool(),
        }

    def test_happy_path(self):
        input_data = self.generate_test_grade_data()
        output_data = GradeDataSerializer(input_data).data

        assert output_data == {
            "isPassing": input_data["isPassing"],
        }


class TestCertificateSerializer(TestCase):
    """Tests for the CertificateSerializer"""

    @classmethod
    def generate_test_certificate_info(cls):
        """Util to generate test certificate info"""
        return {
            "availableDate": random_date(allow_null=True),
            "isRestricted": random_bool(),
            "isAvailable": random_bool(),
            "isEarned": random_bool(),
            "isDownloadable": random_bool(),
            "certPreviewUrl": random_url(allow_null=True),
            "certDownloadUrl": random_url(allow_null=True),
            "honorCertDownloadUrl": random_url(allow_null=True),
        }

    def test_happy_path(self):
        input_data = self.generate_test_certificate_info()
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
            "courseId": f"{uuid4()}",
        }

    @classmethod
    def generate_test_entitlement_info(cls):
        """Util to generate test entitlement info"""
        return {
            "availableSessions": [
                cls.generate_test_session() for _ in range(randint(0, 3))
            ],
            "isRefundable": random_bool(),
            "isFulfilled": random_bool(),
            "canViewCourse": random_bool(),
            "changeDeadline": random_date(),
            "isExpired": random_bool(),
            "expirationDate": random_date(),
        }

    def test_happy_path(self):
        input_data = self.generate_test_entitlement_info()
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
            "expirationDate": datetime_to_django_format(input_data["expirationDate"]),
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

    @classmethod
    def generate_test_programs_info(cls):
        """Util to generate test programs info"""
        return {
            "relatedPrograms": [
                cls.generate_test_related_program() for _ in range(randint(0, 3))
            ],
        }

    def test_happy_path(self):
        input_data = self.generate_test_programs_info()
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

        self.assertDictEqual(output_data, {})

    def test_empty_sessions(self):
        input_data = {"relatedPrograms": []}
        output_data = ProgramsSerializer(input_data).data

        assert output_data == {"relatedPrograms": []}


class TestLearnerEnrollmentsSerializer(LearnerDashboardBaseTest):
    """High-level tests for LearnerEnrollmentsSerializer"""

    def test_happy_path(self):
        """Test that nothing breaks and the output fields look correct"""

        enrollment = self.create_test_enrollment()

        input_data = enrollment
        input_context = {
            "resume_course_urls": {enrollment.course.id: random_url()},
            "ecommerce_payment_page": random_url(),
            "course_mode_info": {
                enrollment.course.id: {
                    "verified_sku": str(uuid4()),
                    "days_for_upsell": randint(0, 14),
                }
            },
        }

        output_data = LearnerEnrollmentSerializer(
            input_data, context=input_context
        ).data

        expected_keys = [
            "courseProvider",
            "course",
            "courseRun",
            "enrollment",
            "gradeData",
            "certificate",
            "entitlements",
            "programs",
        ]
        assert output_data.keys() == set(expected_keys)


class TestUnfulfilledEntitlementSerializer(LearnerDashboardBaseTest):
    """High-level tests for UnfulfilledEntitlementSerializer"""

    @classmethod
    def generate_test_entitlements_data(cls):
        mock_enrollment = cls.create_test_enrollment(cls)

        return {
            "courseProvider": TestCourseProviderSerializer.generate_test_provider_info(),
            "course": mock_enrollment.course,
            "entitlements": TestEntitlementSerializer.generate_test_entitlement_info(),
            "programs": TestProgramsSerializer.generate_test_programs_info(),
        }

    def test_happy_path(self):
        """Test that nothing breaks and the output fields look correct"""
        input_data = self.generate_test_entitlements_data()

        output_data = UnfulfilledEntitlementSerializer(input_data).data

        expected_keys = [
            "courseProvider",
            "course",
            "entitlements",
            "programs",
        ]
        assert output_data.keys() == set(expected_keys)

    def test_allowed_empty(self):
        """Tests for allowed null fields, mostly that nothing breaks"""
        input_data = self.generate_test_entitlements_data()
        input_data["courseProvider"] = None

        output_data = UnfulfilledEntitlementSerializer(input_data).data

        expected_keys = [
            "courseProvider",
            "course",
            "entitlements",
            "programs",
        ]
        assert output_data.keys() == set(expected_keys)


class TestSuggestedCourseSerializer(TestCase):
    """High-level tests for SuggestedCourseSerializer"""

    @classmethod
    def generate_test_suggested_courses(cls):
        return {
            "bannerUrl": random_url(),
            "logoUrl": random_url(),
            "title": f"{uuid4()}",
            "courseUrl": random_url(),
        }

    def test_structure(self):
        """Test that nothing breaks and the output fields look correct"""
        input_data = self.generate_test_suggested_courses()

        output_data = SuggestedCourseSerializer(input_data).data

        expected_keys = [
            "bannerUrl",
            "logoUrl",
            "title",
            "courseUrl",
        ]
        assert output_data.keys() == set(expected_keys)

    def test_happy_path(self):
        """Test that data serializes correctly"""

        input_data = self.generate_test_suggested_courses()

        output_data = SuggestedCourseSerializer(input_data).data

        self.assertDictEqual(
            output_data,
            {
                "bannerUrl": input_data["bannerUrl"],
                "logoUrl": input_data["logoUrl"],
                "title": input_data["title"],
                "courseUrl": input_data["courseUrl"],
            },
        )


class TestEmailConfirmationSerializer(TestCase):
    """High-level tests for EmailConfirmationSerializer"""

    @classmethod
    def generate_test_data(cls):
        return {
            "isNeeded": random_bool(),
            "sendEmailUrl": random_url(),
        }

    def test_structure(self):
        """Test that nothing breaks and the output fields look correct"""
        input_data = self.generate_test_data()

        output_data = EmailConfirmationSerializer(input_data).data

        expected_keys = [
            "isNeeded",
            "sendEmailUrl",
        ]
        assert output_data.keys() == set(expected_keys)

    def test_happy_path(self):
        """Test that data serializes correctly"""

        input_data = self.generate_test_data()

        output_data = EmailConfirmationSerializer(input_data).data

        self.assertDictEqual(
            output_data,
            {
                "isNeeded": input_data["isNeeded"],
                "sendEmailUrl": input_data["sendEmailUrl"],
            },
        )


class TestEnterpriseDashboardsSerializer(TestCase):
    """High-level tests for EnterpriseDashboardsSerializer"""

    @classmethod
    def generate_test_dashboard(cls):
        return {
            "label": f"{uuid4()}",
            "url": random_url(),
        }

    @classmethod
    def generate_test_data(cls):
        return {
            "availableDashboards": [
                cls.generate_test_dashboard() for _ in range(randint(0, 3))
            ],
            "mostRecentDashboard": cls.generate_test_dashboard()
            if random_bool()
            else None,
        }

    def test_structure(self):
        """Test that nothing breaks and the output fields look correct"""
        input_data = self.generate_test_data()

        output_data = EnterpriseDashboardsSerializer(input_data).data

        expected_keys = [
            "availableDashboards",
            "mostRecentDashboard",
        ]
        assert output_data.keys() == set(expected_keys)

    def test_happy_path(self):
        """Test that data serializes correctly"""

        input_data = self.generate_test_data()

        output_data = EnterpriseDashboardsSerializer(input_data).data

        self.assertDictEqual(
            output_data,
            {
                "availableDashboards": input_data["availableDashboards"],
                "mostRecentDashboard": input_data["mostRecentDashboard"],
            },
        )


class TestLearnerDashboardSerializer(LearnerDashboardBaseTest):
    """High-level tests for Learner Dashboard serialization"""

    # Show full diff for serialization issues
    maxDiff = None

    def test_empty(self):
        """Test that empty inputs return the right keys"""

        input_data = {
            "emailConfirmation": None,
            "enterpriseDashboards": None,
            "platformSettings": None,
            "enrollments": [],
            "unfulfilledEntitlements": [],
            "suggestedCourses": [],
        }
        output_data = LearnerDashboardSerializer(input_data).data

        self.assertDictEqual(
            output_data,
            {
                "emailConfirmation": None,
                "enterpriseDashboards": None,
                "platformSettings": None,
                "enrollments": [],
                "unfulfilledEntitlements": [],
                "suggestedCourses": [],
            },
        )

    def test_enrollments(self):
        """Test that enrollments-related info is linked and serialized correctly"""

        enrollments = [self.create_test_enrollment()]

        resume_course_urls = {
            enrollment.course.id: random_url() for enrollment in enrollments
        }
        course_mode_info = {
            enrollment.course.id: {
                "verified_sku": str(uuid4()),
                "days_for_upsell": randint(0, 14),
            }
            for enrollment in enrollments
            if enrollment.mode == "audit"
        }

        input_data = {
            "emailConfirmation": None,
            "enterpriseDashboards": None,
            "platformSettings": None,
            "enrollments": enrollments,
            "unfulfilledEntitlements": [],
            "suggestedCourses": [],
        }

        input_context = {
            "resume_course_urls": resume_course_urls,
            "ecommerce_payment_page": random_url(),
            "course_mode_info": course_mode_info,
        }

        output_data = LearnerDashboardSerializer(input_data, context=input_context).data

        # Right now just make sure nothing broke
        serialized_enrollments = output_data.pop("enrollments")
        assert serialized_enrollments is not None

    @mock.patch(
        "lms.djangoapps.learner_dashboard.serializers.SuggestedCourseSerializer.to_representation"
    )
    @mock.patch(
        "lms.djangoapps.learner_dashboard.serializers.UnfulfilledEntitlementSerializer.to_representation"
    )
    @mock.patch(
        "lms.djangoapps.learner_dashboard.serializers.LearnerEnrollmentSerializer.to_representation"
    )
    @mock.patch(
        "lms.djangoapps.learner_dashboard.serializers.PlatformSettingsSerializer.to_representation"
    )
    @mock.patch(
        "lms.djangoapps.learner_dashboard.serializers.EnterpriseDashboardsSerializer.to_representation"
    )
    @mock.patch(
        "lms.djangoapps.learner_dashboard.serializers.EmailConfirmationSerializer.to_representation"
    )
    def test_linkage(
        self,
        mock_email_confirmation_serializer,
        mock_enterprise_dashboards_serializer,
        mock_platform_settings_serializer,
        mock_learner_enrollment_serializer,
        mock_entitlements_serializer,
        mock_suggestions_serializer,
    ):
        mock_email_confirmation_serializer.return_value = (
            mock_email_confirmation_serializer
        )
        mock_enterprise_dashboards_serializer.return_value = (
            mock_enterprise_dashboards_serializer
        )
        mock_platform_settings_serializer.return_value = (
            mock_platform_settings_serializer
        )
        mock_learner_enrollment_serializer.return_value = (
            mock_learner_enrollment_serializer
        )
        mock_entitlements_serializer.return_value = mock_entitlements_serializer
        mock_suggestions_serializer.return_value = mock_suggestions_serializer

        input_data = {
            "emailConfirmation": {},
            "enterpriseDashboards": [{}],
            "platformSettings": {},
            "enrollments": [{}],
            "unfulfilledEntitlements": [{}],
            "suggestedCourses": [{}],
        }
        output_data = LearnerDashboardSerializer(input_data).data

        self.assertDictEqual(
            output_data,
            {
                "emailConfirmation": mock_email_confirmation_serializer,
                "enterpriseDashboards": mock_enterprise_dashboards_serializer,
                "platformSettings": mock_platform_settings_serializer,
                "enrollments": [mock_learner_enrollment_serializer],
                "unfulfilledEntitlements": [mock_entitlements_serializer],
                "suggestedCourses": [mock_suggestions_serializer],
            },
        )
