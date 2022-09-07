"""Tests for serializers for the Learner Dashboard"""

from datetime import date, datetime, timedelta
from itertools import product
from random import randint
from unittest import mock
from uuid import uuid4

from django.conf import settings
from django.test import TestCase
import ddt

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.course_modes.tests.factories import CourseModeFactory
from common.djangoapps.entitlements.tests.factories import CourseEntitlementFactory
from common.djangoapps.student.tests.factories import (
    CourseEnrollmentFactory,
    UserFactory,
)
from openedx.core.djangoapps.catalog.tests.factories import CourseRunFactory as CatalogCourseRunFactory
from lms.djangoapps.learner_home.serializers import (
    CertificateSerializer,
    CourseProviderSerializer,
    CourseRunSerializer,
    CourseSerializer,
    EmailConfirmationSerializer,
    EnrollmentSerializer,
    EnterpriseDashboardSerializer,
    EntitlementSerializer,
    GradeDataSerializer,
    HasAccessSerializer,
    LearnerEnrollmentSerializer,
    PlatformSettingsSerializer,
    ProgramsSerializer,
    LearnerDashboardSerializer,
    SuggestedCourseSerializer,
    UnfulfilledEntitlementSerializer,
)
from lms.djangoapps.learner_home.test_utils import (
    datetime_to_django_format,
    random_bool,
    random_date,
    random_url,
)
from xmodule.data import CertificatesDisplayBehaviors
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class LearnerDashboardBaseTest(SharedModuleStoreTestCase):
    """Base class for common setup"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory()

    def create_test_enrollment(self, course_mode=CourseMode.AUDIT):
        """Create a test user, course, and enrollment. Return the enrollment."""
        course = CourseFactory(self_paced=True)
        CourseModeFactory(
            course_id=course.id,
            mode_slug=course_mode,
        )

        test_enrollment = CourseEnrollmentFactory(course_id=course.id, mode=course_mode)

        # Add extra info to exercise serialization
        test_enrollment.course_overview.marketing_url = random_url()
        test_enrollment.course_overview.end = random_date()
        test_enrollment.course_overview.certificate_available_date = random_date()

        return test_enrollment

    def _assert_all_keys_equal(self, dicts):
        element_0 = dicts[0]
        for element in dicts[1:]:
            assert element_0.keys() == element.keys()


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


class TestCourseProviderSerializer(LearnerDashboardBaseTest):
    """Tests for the CourseProviderSerializer"""

    @classmethod
    def generate_test_provider_info(cls):
        """Util to generate test provider info"""
        return {
            "name": f"{uuid4()}",
        }

    def test_happy_path(self):
        test_enrollment = self.create_test_enrollment()

        input_data = test_enrollment.course_overview
        output_data = CourseProviderSerializer(input_data).data

        self.assertEqual(output_data["name"], test_enrollment.course_overview.org)


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


@ddt.ddt
class TestHasAccessSerializer(LearnerDashboardBaseTest):
    """Tests for the HasAccessSerializer"""

    def create_test_context(self, course):
        return {
            "course_access_checks": {
                course.id: {
                    "has_unmet_prerequisites": False,
                    "is_too_early_to_view": False,
                    "user_has_staff_access": False,
                }
            }
        }

    @ddt.data(True, False)
    def test_unmet_prerequisites(self, has_unmet_prerequisites):
        # Given an enrollment
        input_data = self.create_test_enrollment()
        input_context = self.create_test_context(input_data.course)

        # ... without unmet prerequisites
        if has_unmet_prerequisites:
            # ... or with unmet prerequisites
            prerequisite_course = CourseFactory()
            input_context.update(
                {
                    "course_access_checks": {
                        input_data.course.id: {
                            "has_unmet_prerequisites": has_unmet_prerequisites,
                        }
                    }
                }
            )

        # When I serialize
        output_data = HasAccessSerializer(input_data, context=input_context).data

        # Then "hasUnmetPrerequisites" is outputs correctly
        self.assertEqual(output_data["hasUnmetPrerequisites"], has_unmet_prerequisites)

    @ddt.data(True, False)
    def test_is_staff(self, is_staff):
        # Given an enrollment
        input_data = self.create_test_enrollment()
        input_context = self.create_test_context(input_data.course)

        # Where user has/hasn't staff access
        input_context.update(
            {
                "course_access_checks": {
                    input_data.course.id: {
                        "user_has_staff_access": is_staff,
                    }
                }
            }
        )

        # When I serialize
        output_data = HasAccessSerializer(input_data, context=input_context).data

        # Then "isStaff" serializes properly
        self.assertEqual(output_data["isStaff"], is_staff)

    @ddt.data(True, False)
    def test_is_too_early(self, is_too_early):
        # Given an enrollment
        input_data = self.create_test_enrollment()
        input_context = self.create_test_context(input_data.course)

        # Where the course is/n't yet open for a learner
        input_context.update(
            {
                "course_access_checks": {
                    input_data.course.id: {
                        "is_too_early_to_view": is_too_early,
                    }
                }
            }
        )

        # When I serialize
        output_data = HasAccessSerializer(input_data, context=input_context).data

        # Then "isTooEarly" serializes properly
        self.assertEqual(output_data["isTooEarly"], is_too_early)


@ddt.ddt
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
            "show_email_settings_for": [course.id],
            "show_courseware_link": {course.id: {"has_access": True}},
            "resume_course_urls": {course.id: "some_url"},
            "use_ecommerce_payment_flow": True,
        }

    def serialize_test_enrollment(self):
        """
        Create a test enrollment, pass it to EnrollmentSerializer, and return the serialized data
        """
        input_data = self.create_test_enrollment()
        input_context = self.create_test_context(input_data.course)

        serializer = EnrollmentSerializer(input_data, context=input_context)
        return serializer.data

    def test_with_data(self):
        output = self.serialize_test_enrollment()
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

        assert output["isAuditAccessExpired"] is True

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
        assert output["canUpgrade"] is True

    @ddt.data(None, "some_url")
    def test_has_started(self, resume_url):
        # Given the presence or lack of a resume_course_url
        input_data = self.create_test_enrollment()
        input_context = self.create_test_context(input_data.course)

        input_context.update(
            {
                "resume_course_urls": {
                    input_data.course.id: resume_url,
                }
            }
        )

        # When I get "hasStarted"
        output = EnrollmentSerializer(input_data, context=input_context).data

        # If I have a resume URL, "hasStarted" should be True, otherwise False
        if resume_url:
            self.assertTrue(output["hasStarted"])
        else:
            self.assertFalse(output["hasStarted"])


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


@ddt.ddt
class TestCertificateSerializer(LearnerDashboardBaseTest):
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

    def create_test_context(self, course):
        """Get a test context object with an available certificate"""
        return {
            "cert_statuses": {
                course.id: {
                    "cert_web_view_url": random_url(),
                    "status": "downloadable",
                    "show_cert_web_view": True,
                }
            }
        }

    def test_with_data(self):
        """Simple mappings test for a course with an available certificate"""
        # Given a verified enrollment
        input_data = self.create_test_enrollment(course_mode=CourseMode.VERIFIED)

        # ... with a certificate
        input_context = self.create_test_context(input_data.course)

        # ... and some data preemptively gathered
        available_date = random_date()
        input_data.course.certificate_available_date = available_date
        cert_url = input_context["cert_statuses"][input_data.course.id][
            "cert_web_view_url"
        ]

        # When I get certificate info
        output_data = CertificateSerializer(input_data, context=input_context).data

        # Then all the info is provided correctly
        self.assertDictEqual(
            output_data,
            {
                "availableDate": datetime_to_django_format(available_date),
                "isRestricted": False,
                "isEarned": True,
                "isDownloadable": True,
                "certPreviewUrl": cert_url,
            },
        )

    @mock.patch.dict(settings.FEATURES, ENABLE_V2_CERT_DISPLAY_SETTINGS=False)
    def test_available_date_old_format(self):
        # Given new cert display settings are not enabled
        input_data = self.create_test_enrollment(course_mode=CourseMode.VERIFIED)
        input_data.course.certificate_available_date = random_date()
        input_context = self.create_test_context(input_data.course)

        # When I get certificate info
        output_data = CertificateSerializer(input_data, context=input_context).data

        # Then the available date is defaulted to the certificate available date
        expected_available_date = datetime_to_django_format(
            input_data.course.certificate_available_date
        )
        self.assertEqual(output_data["availableDate"], expected_available_date)

    @mock.patch.dict(settings.FEATURES, ENABLE_V2_CERT_DISPLAY_SETTINGS=True)
    def test_available_date_course_end(self):
        # Given new cert display settings are enabled
        input_data = self.create_test_enrollment(course_mode=CourseMode.VERIFIED)
        input_context = self.create_test_context(input_data.course)

        # ... and certificate display behavior is set to the course end date
        input_data.course.certificates_display_behavior = (
            CertificatesDisplayBehaviors.END
        )

        # When I try to get cert available date
        output_data = CertificateSerializer(input_data, context=input_context).data

        # Then the available date is the course end date
        expected_available_date = datetime_to_django_format(input_data.course.end)
        self.assertEqual(output_data["availableDate"], expected_available_date)

    @mock.patch.dict(settings.FEATURES, ENABLE_V2_CERT_DISPLAY_SETTINGS=True)
    def test_available_date_specific_end(self):
        # Given new cert display settings are enabled
        input_data = self.create_test_enrollment(course_mode=CourseMode.VERIFIED)
        input_context = self.create_test_context(input_data.course)

        # ... and certificate display behavior is set to a specified date
        input_data.course.certificate_available_date = random_date()
        input_data.course.certificates_display_behavior = (
            CertificatesDisplayBehaviors.END_WITH_DATE
        )

        # When I try to get cert available date
        output_data = CertificateSerializer(input_data, context=input_context).data

        # Then the available date is the course end date
        expected_available_date = datetime_to_django_format(
            input_data.course.certificate_available_date
        )
        self.assertEqual(output_data["availableDate"], expected_available_date)

    @ddt.data(
        ("downloadable", False),
        ("notpassing", False),
        ("restricted", True),
        ("auditing", False),
    )
    @ddt.unpack
    def test_is_restricted(self, cert_status, is_restricted_expected):
        """Test for isRestricted field"""
        # Given a verified enrollment with a certificate
        input_data = self.create_test_enrollment(course_mode=CourseMode.VERIFIED)
        input_context = self.create_test_context(input_data.course)

        # ... and a cert status {cert_status}
        input_context["cert_statuses"][input_data.course.id]["status"] = cert_status

        # When I get certificate info
        output_data = CertificateSerializer(input_data, context=input_context).data

        # Then isRestricted should be calculated correctly
        self.assertEqual(output_data["isRestricted"], is_restricted_expected)

    @ddt.data(
        ("downloadable", True),
        ("notpassing", False),
        ("restricted", False),
        ("auditing", False),
        ("certificate_earned_but_not_available", True),
    )
    @ddt.unpack
    def test_is_earned(self, cert_status, is_earned_expected):
        """Test for isEarned field"""
        # Given a verified enrollment with a certificate
        input_data = self.create_test_enrollment(course_mode=CourseMode.VERIFIED)
        input_context = self.create_test_context(input_data.course)

        # ... and a cert status {cert_status}
        input_context["cert_statuses"][input_data.course.id]["status"] = cert_status

        # When I get certificate info
        output_data = CertificateSerializer(input_data, context=input_context).data

        # Then isEarned should be calculated correctly
        self.assertEqual(output_data["isEarned"], is_earned_expected)

    @ddt.data(
        ("downloadable", True),
        ("notpassing", False),
        ("restricted", False),
        ("auditing", False),
        ("certificate_earned_but_not_available", False),
    )
    @ddt.unpack
    def test_is_downloadable(self, cert_status, is_downloadable_expected):
        """Test for isDownloadable field"""
        # Given a verified enrollment with a certificate
        input_data = self.create_test_enrollment(course_mode=CourseMode.VERIFIED)
        input_context = self.create_test_context(input_data.course)

        # ... and a cert status {cert_status}
        input_context["cert_statuses"][input_data.course.id]["status"] = cert_status

        # When I get certificate info
        output_data = CertificateSerializer(input_data, context=input_context).data

        # Then isDownloadable should be calculated correctly
        self.assertEqual(output_data["isDownloadable"], is_downloadable_expected)

    @ddt.data(
        (True, random_url()),
        (False, random_url()),
        (True, None),
        (False, None),
    )
    @ddt.unpack
    def test_cert_preview_url(self, show_cert_web_view, cert_web_view_url):
        """Test for certPreviewUrl field"""
        # Given a verified enrollment with a certificate
        input_data = self.create_test_enrollment(course_mode=CourseMode.VERIFIED)
        input_context = self.create_test_context(input_data.course)

        # ... and settings show_cert_web_view and cert_web_view_url
        input_context["cert_statuses"][input_data.course.id][
            "show_cert_web_view"
        ] = show_cert_web_view
        input_context["cert_statuses"][input_data.course.id][
            "cert_web_view_url"
        ] = cert_web_view_url

        # When I get certificate info
        output_data = CertificateSerializer(input_data, context=input_context).data

        # Then certPreviewUrl should be calculated correctly
        self.assertEqual(
            output_data["certPreviewUrl"],
            cert_web_view_url if show_cert_web_view else None,
        )


@ddt.ddt
class TestEntitlementSerializer(TestCase):
    """Tests for the EntitlementSerializer"""

    def _assert_availale_sessions(self, input_sessions, output_sessions):
        assert len(output_sessions) == len(input_sessions)
        for input_session, output_session in zip(input_sessions, output_sessions):
            assert output_session == {
                'startDate': input_session['start'],
                'endDate': input_session['end'],
                'courseId': input_session['key']
            }

    @ddt.unpack
    @ddt.idata(product([True, False], repeat=2))
    def test_serialize_entitlement(self, isExpired, isEnrolled):
        entitlement_kwargs = {}
        if isExpired:
            entitlement_kwargs['expired_at'] = datetime.now()
        if isEnrolled:
            entitlement_kwargs['enrollment_course_run'] = CourseEnrollmentFactory.create()
        entitlement = CourseEntitlementFactory.create(**entitlement_kwargs)
        available_sessions = CatalogCourseRunFactory.create_batch(4)
        course_entitlement_available_sessions = {
            str(entitlement.uuid): available_sessions
        }

        output_data = EntitlementSerializer(entitlement, context={
            'course_entitlement_available_sessions': course_entitlement_available_sessions
        }).data

        output_sessions = output_data.pop('availableSessions')
        self._assert_availale_sessions(available_sessions, output_sessions)

        if isExpired:
            expected_expiration_date = entitlement.expired_at
        else:
            expected_expiration_date = date.today() + timedelta(days=entitlement.get_days_until_expiration())

        assert output_data == {
            "isRefundable": entitlement.is_entitlement_refundable(),
            "isFulfilled": bool(entitlement.enrollment_course_run),
            "changeDeadline": expected_expiration_date,
            "isExpired": bool(entitlement.expired_at),
            "expirationDate": expected_expiration_date,
            "uuid": str(entitlement.uuid),
            "enrollmentUrl": f"/api/entitlements/v1/entitlements/{entitlement.uuid}/enrollments"
        }


class TestProgramsSerializer(TestCase):
    """Tests for the ProgramsSerializer and RelatedProgramsSerializer"""

    @classmethod
    def generate_test_related_program(cls):
        """Generate a program with random test data"""
        return {
            "bannerUrl": random_url(),
            "estimatedNumberOfWeeks": randint(0, 45),
            "logoUrl": random_url(),
            "numberOfCourses": randint(0, 100),
            "programType": f"{uuid4()}",
            "programUrl": random_url(),
            "provider": f"{uuid4()} Inc.",
            "title": f"{uuid4()}",
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
                "bannerUrl": input_program["bannerUrl"],
                "estimatedNumberOfWeeks": input_program["estimatedNumberOfWeeks"],
                "logoUrl": input_program["logoUrl"],
                "numberOfCourses": input_program["numberOfCourses"],
                "programType": input_program["programType"],
                "programUrl": input_program["programUrl"],
                "provider": input_program["provider"],
                "title": input_program["title"],
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
            "fulfilled_entitlements": {},
            "unfulfilled_entitlement_pseudo_sessions": {},
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
            "entitlement",
            "programs",
        ]
        assert output_data.keys() == set(expected_keys)


class TestUnfulfilledEntitlementSerializer(LearnerDashboardBaseTest):
    """High-level tests for UnfulfilledEntitlementSerializer"""

    @classmethod
    def generate_test_entitlement_data(cls):
        mock_enrollment = cls.create_test_enrollment(cls)

        return {
            "courseProvider": TestCourseProviderSerializer.generate_test_provider_info(),
            "course": mock_enrollment.course,
            "entitlement": TestEntitlementSerializer.generate_test_entitlement_info(),
            "programs": TestProgramsSerializer.generate_test_programs_info(),
        }

    def test_happy_path(self):
        """Test that nothing breaks and the output fields look correct"""
        unfulfilled_entitlement = CourseEntitlementFactory.create()
        pseudo_sessions = {str(unfulfilled_entitlement.uuid): CatalogCourseRunFactory.create()}
        available_sessions = {str(unfulfilled_entitlement.uuid): CatalogCourseRunFactory.create_batch(3)}
        context = {
            'unfulfilled_entitlement_pseudo_sessions': pseudo_sessions,
            'course_entitlement_available_sessions': available_sessions,
        }

        output_data = UnfulfilledEntitlementSerializer(unfulfilled_entitlement, context=context).data

        expected_keys = [
            "courseProvider",
            "course",
            "entitlement",
            "programs",
            "courseRun",
            "gradeData",
            "certificate",
            "enrollment"
        ]

        assert output_data.keys() == set(expected_keys)
        assert output_data['courseRun'] is None
        assert output_data['gradeData'] is None
        assert output_data['certificate'] is None
        assert output_data['enrollment'] == UnfulfilledEntitlementSerializer.STATIC_ENTITLEMENT_ENROLLMENT_DATA

    def test_static_enrollment_data(self):
        """
        For an unfulfilled entitlement's "enrollment" data, we're returning a static dict.
        This test is to ensure that that dict has the same keys as returned by the LearnerEnrollmentSerializer
        """
        output_data = TestEnrollmentSerializer().serialize_test_enrollment()
        expected_keys = UnfulfilledEntitlementSerializer.STATIC_ENTITLEMENT_ENROLLMENT_DATA.keys()
        actual_keys = output_data.keys()
        assert expected_keys == actual_keys


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


class TestEnterpriseDashboardSerializer(TestCase):
    """High-level tests for EnterpriseDashboardSerializer"""

    @classmethod
    def generate_test_data(cls):
        return {
            "uuid": str(uuid4()),
            "name": str(uuid4()),
        }

    def test_structure(self):
        """Test that nothing breaks and the output fields look correct"""
        input_data = self.generate_test_data()

        output_data = EnterpriseDashboardSerializer(input_data).data

        expected_keys = [
            "label",
            "url",
        ]
        assert output_data.keys() == set(expected_keys)

    def test_happy_path(self):
        """Test that data serializes correctly"""

        input_data = self.generate_test_data()

        output_data = EnterpriseDashboardSerializer(input_data).data

        self.assertDictEqual(
            output_data,
            {
                "label": input_data["name"],
                "url": settings.ENTERPRISE_LEARNER_PORTAL_BASE_URL + '/' + input_data["uuid"],
            },
        )


class TestLearnerDashboardSerializer(LearnerDashboardBaseTest):
    """High-level tests for Learner Dashboard serialization"""

    # Show full diff for serialization issues
    maxDiff = None

    def make_test_context(self, enrollments=None, enrollments_with_entitlements=None, unfulfilled_entitlements=None):
        """
        Given enrollments and entitlements, generate a mathing serializer context
        """
        enrollments = enrollments or []
        enrollments_with_entitlements = enrollments_with_entitlements or []
        unfulfilled_entitlements = unfulfilled_entitlements or []

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

        all_entitlements = list(unfulfilled_entitlements)
        fulfilled_entitlements = {}
        for enrollment in enrollments_with_entitlements:
            entitlement = CourseEntitlementFactory.create(
                enrollment_course_run=enrollment
            )
            all_entitlements.append(entitlement)
            fulfilled_entitlements[str(enrollment.course_id)] = entitlement

        unfulfilled_entitlement_pseudo_sessions = {
            str(unfulfilled_entitlement.uuid): CatalogCourseRunFactory.create()
            for unfulfilled_entitlement in unfulfilled_entitlements
        }

        course_entitlement_available_sessions = {
            str(entitlement.uuid): CatalogCourseRunFactory.create_batch(3)
            for entitlement in all_entitlements
        }

        input_context = {
            "resume_course_urls": resume_course_urls,
            "ecommerce_payment_page": random_url(),
            "course_mode_info": course_mode_info,
            "fulfilled_entitlements": fulfilled_entitlements,
            "unfulfilled_entitlement_pseudo_sessions": unfulfilled_entitlement_pseudo_sessions,
            "course_entitlement_available_sessions": course_entitlement_available_sessions,
        }
        return input_context

    def test_empty(self):
        """Test that empty inputs return the right keys"""

        input_data = {
            "emailConfirmation": None,
            "enterpriseDashboard": None,
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
                "enterpriseDashboard": None,
                "platformSettings": None,
                "courses": [],
                "suggestedCourses": [],
            },
        )

    def test_enrollments(self):
        """Test that enrollments-related info is linked and serialized correctly"""

        enrollments = [self.create_test_enrollment()]

        input_context = self.make_test_context(
            enrollments=enrollments,
        )

        input_data = {
            "emailConfirmation": None,
            "enterpriseDashboard": None,
            "platformSettings": None,
            "enrollments": enrollments,
            "unfulfilledEntitlements": [],
            "suggestedCourses": [],
        }

        output_data = LearnerDashboardSerializer(input_data, context=input_context).data

        # Right now just make sure nothing broke
        courses = output_data.pop("courses")
        assert courses is not None

    def test_entitlements(self):
        # One standard enrollment, one fulfilled entitlement, one unfulfilled enrollment
        enrollments = [
            self.create_test_enrollment(),
            self.create_test_enrollment()
        ]
        unfulfilled_entitlements = [CourseEntitlementFactory.create()]

        input_context = self.make_test_context(
            enrollments=enrollments,
            enrollments_with_entitlements=[enrollments[1]],
            unfulfilled_entitlements=unfulfilled_entitlements,
        )

        input_data = {
            "emailConfirmation": None,
            "enterpriseDashboards": None,
            "platformSettings": None,
            "enrollments": enrollments,
            "unfulfilledEntitlements": unfulfilled_entitlements,
            "suggestedCourses": [],
        }

        output_data = LearnerDashboardSerializer(input_data, context=input_context).data

        courses = output_data.pop("courses")
        # We should have three dicts with identical keys for the course card elements
        assert len(courses) == 3
        self._assert_all_keys_equal(courses)
        # Non-entitlement enrollment should have no entitlement info
        assert not courses[0]['entitlement']
        # Fulfuilled and Unfulfilled entitlement should have identical keys
        fulfilled_entitlement = courses[1]['entitlement']
        unfulfilled_entitlement = courses[2]['entitlement']
        assert fulfilled_entitlement
        assert unfulfilled_entitlement
        assert fulfilled_entitlement.keys() == unfulfilled_entitlement.keys()

    @mock.patch(
        "lms.djangoapps.learner_home.serializers.SuggestedCourseSerializer.to_representation"
    )
    @mock.patch(
        "lms.djangoapps.learner_home.serializers.UnfulfilledEntitlementSerializer.data"
    )
    @mock.patch(
        "lms.djangoapps.learner_home.serializers.LearnerEnrollmentSerializer.data"
    )
    @mock.patch(
        "lms.djangoapps.learner_home.serializers.PlatformSettingsSerializer.to_representation"
    )
    @mock.patch(
        "lms.djangoapps.learner_home.serializers.EnterpriseDashboardSerializer.to_representation"
    )
    @mock.patch(
        "lms.djangoapps.learner_home.serializers.EmailConfirmationSerializer.to_representation"
    )
    def test_linkage(
        self,
        mock_email_confirmation_serializer,
        mock_enterprise_dashboard_serializer,
        mock_platform_settings_serializer,
        mock_learner_enrollment_serializer,
        mock_entitlement_serializer,
        mock_suggestions_serializer,
    ):
        mock_email_confirmation_serializer.return_value = (
            mock_email_confirmation_serializer
        )
        mock_enterprise_dashboard_serializer.return_value = (
            mock_enterprise_dashboard_serializer
        )
        mock_platform_settings_serializer.return_value = (
            mock_platform_settings_serializer
        )
        mock_learner_enrollment_serializer.return_value = (
            mock_learner_enrollment_serializer
        )
        mock_entitlement_serializer.return_value = mock_entitlement_serializer
        mock_suggestions_serializer.return_value = mock_suggestions_serializer

        input_data = {
            "emailConfirmation": {},
            "enterpriseDashboard": {},
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
                "enterpriseDashboard": mock_enterprise_dashboard_serializer,
                "platformSettings": mock_platform_settings_serializer,
                "courses": [
                    mock_learner_enrollment_serializer,
                    mock_entitlement_serializer,
                ],
                "suggestedCourses": [mock_suggestions_serializer],
            },
        )
