"""Test for learner views and related functions"""

from contextlib import contextmanager
import json
from unittest import TestCase
from unittest.mock import patch
from uuid import uuid4

import ddt
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from lms.djangoapps.learner_home.test_utils import create_test_enrollment
from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.entitlements.tests.factories import CourseEntitlementFactory
from common.djangoapps.student.tests.factories import (
    CourseEnrollmentFactory,
    UserFactory,
)
from lms.djangoapps.bulk_email.models import Optout
from lms.djangoapps.learner_home.views import (
    get_email_settings_info,
    get_enrollments,
    get_platform_settings,
    get_user_account_confirmation_info,
    get_entitlements,
)
from lms.djangoapps.learner_home.test_serializers import random_url
from openedx.core.djangoapps.catalog.tests.factories import CourseRunFactory as CatalogCourseRunFactory
from xmodule.modulestore.tests.django_utils import (
    TEST_DATA_SPLIT_MODULESTORE,
    SharedModuleStoreTestCase,
)
from xmodule.modulestore.tests.factories import CourseFactory


ENTERPRISE_ENABLED = "ENABLE_ENTERPRISE_INTEGRATION"


class TestGetPlatformSettings(TestCase):
    """Tests for get_platform_settings"""

    MOCK_SETTINGS = {
        "DEFAULT_FEEDBACK_EMAIL": f"{uuid4()}@example.com",
        "PAYMENT_SUPPORT_EMAIL": f"{uuid4()}@example.com",
    }

    @patch.multiple("django.conf.settings", **MOCK_SETTINGS)
    @patch("lms.djangoapps.learner_home.views.marketing_link")
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


@ddt.ddt
class TestGetUserAccountConfirmationInfo(SharedModuleStoreTestCase):
    """Tests for get_user_account_confirmation_info"""

    MOCK_SETTINGS = {
        "ACTIVATION_EMAIL_SUPPORT_LINK": "activation.example.com",
        "SUPPORT_SITE_LINK": "support.example.com",
    }

    @classmethod
    def mock_response(cls):
        return {
            "isNeeded": False,
            "sendEmailUrl": random_url(),
        }

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    @patch.multiple("django.conf.settings", **MOCK_SETTINGS)
    @ddt.data(True, False)
    def test_is_needed(self, user_is_active):
        """Email confirmation is needed when the user is not active"""
        self.user.is_active = user_is_active

        user_account_confirmation_info = get_user_account_confirmation_info(self.user)

        assert user_account_confirmation_info["isNeeded"] == (not user_is_active)

    @patch(
        "django.conf.settings.ACTIVATION_EMAIL_SUPPORT_LINK",
        MOCK_SETTINGS["ACTIVATION_EMAIL_SUPPORT_LINK"],
    )
    def test_email_url_support_link(self):
        # Given an ACTIVATION_EMAIL_SUPPORT_LINK is supplied
        # When I get user account confirmation info
        user_account_confirmation_info = get_user_account_confirmation_info(self.user)

        # Then that link should be returned as the sendEmailUrl
        self.assertEqual(
            user_account_confirmation_info["sendEmailUrl"],
            self.MOCK_SETTINGS["ACTIVATION_EMAIL_SUPPORT_LINK"],
        )

    @patch("lms.djangoapps.learner_home.views.configuration_helpers")
    @patch("django.conf.settings.SUPPORT_SITE_LINK", MOCK_SETTINGS["SUPPORT_SITE_LINK"])
    def test_email_url_support_fallback_link(self, mock_config_helpers):
        # Given an ACTIVATION_EMAIL_SUPPORT_LINK is NOT supplied
        mock_config_helpers.get_value.return_value = None

        # When I get user account confirmation info
        user_account_confirmation_info = get_user_account_confirmation_info(self.user)

        # Then sendEmailUrl falls back to SUPPORT_SITE_LINK
        self.assertEqual(
            user_account_confirmation_info["sendEmailUrl"],
            self.MOCK_SETTINGS["SUPPORT_SITE_LINK"],
        )


class TestGetEnrollments(SharedModuleStoreTestCase):
    """Tests for get_enrollments"""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_basic(self):
        # Given a set of enrollments
        test_enrollments = [create_test_enrollment(self.user) for i in range(3)]

        # When I request my enrollments
        returned_enrollments, course_mode_info = get_enrollments(self.user, None, None)

        # Then I return those enrollments and course mode info
        assert len(returned_enrollments) == len(test_enrollments)
        assert len(course_mode_info.keys()) == len(test_enrollments)

        # ... with enrollments and course info
        for enrollment in test_enrollments:
            assert enrollment.course_id in course_mode_info
            assert enrollment in returned_enrollments

    def test_empty(self):
        # Given a user has no enrollments
        # When they request enrollments
        returned_enrollments, course_mode_info = get_enrollments(self.user, None, None)

        # Then I return an empty list and dict
        self.assertEqual(returned_enrollments, [])
        self.assertEqual(course_mode_info, {})


class TestGetEntitlements(SharedModuleStoreTestCase):
    """Tests for get_entitlements"""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    @contextmanager
    def mock_get_filtered_course_entitlements(
        self,
        filtered_entitlements,
        course_entitlement_available_sessions,
        unfulfilled_entitlement_pseudo_sessions
    ):
        """
        Context manager utility for mocking get_filtered_course_entitlements.
        This function calls out to multiple external services and is tested elsewhere.
        """
        return_value = (
            filtered_entitlements,
            course_entitlement_available_sessions,
            unfulfilled_entitlement_pseudo_sessions,
        )
        with patch('lms.djangoapps.learner_home.views.get_filtered_course_entitlements', return_value=return_value):
            yield

    def create_test_fulfilled_entitlement(self):
        enrollment = CourseEnrollmentFactory(user=self.user, is_active=True)
        return CourseEntitlementFactory.create(
            user=self.user, enrollment_course_run=enrollment
        )

    def create_test_unfulfilled_entitlement(self):
        return CourseEntitlementFactory.create(user=self.user)

    def create_test_entitlement(self):
        """create an entitlement course for the user"""
        enrollment = CourseEnrollmentFactory(user=self.user, is_active=True)
        return CourseEntitlementFactory.create(
            user=self.user, enrollment_course_run=enrollment, expired_at=timezone.now()
        )

    def test_basic(self):
        fulfilled_test_entitlements = [
            self.create_test_fulfilled_entitlement() for _ in range(2)
        ]
        unfulfilled_test_entitlements = [
            self.create_test_unfulfilled_entitlement() for _ in range(3)
        ]

        available_sessions = {}
        for entitlement in fulfilled_test_entitlements + unfulfilled_test_entitlements:
            available_sessions[str(entitlement.uuid)] = CatalogCourseRunFactory.create_batch(3)

        pseudo_sessions = {}
        for entitlement in unfulfilled_test_entitlements:
            pseudo_sessions[str(entitlement.uuid)] = CatalogCourseRunFactory.create()

        with self.mock_get_filtered_course_entitlements(
            fulfilled_test_entitlements + unfulfilled_test_entitlements,
            available_sessions,
            pseudo_sessions
        ):
            (
                fulfilled_entitlements_by_course_key,
                unfulfilled_entitlements,
                course_entitlement_available_sessions,
                unfulfilled_entitlement_pseudo_sessions,
            ) = get_entitlements(self.user, None, None)

        assert len(fulfilled_entitlements_by_course_key) == len(fulfilled_test_entitlements)
        assert len(unfulfilled_entitlements) == len(unfulfilled_test_entitlements)
        assert set(unfulfilled_entitlements) == set(unfulfilled_test_entitlements)
        assert course_entitlement_available_sessions is available_sessions
        assert unfulfilled_entitlement_pseudo_sessions is pseudo_sessions

        for fulfilled_entitlement in fulfilled_test_entitlements:
            course_id = str(fulfilled_entitlement.enrollment_course_run.course.id)
            entitlement = fulfilled_entitlements_by_course_key[course_id]
            assert entitlement is fulfilled_entitlement

    def test_empty(self):
        with self.mock_get_filtered_course_entitlements([], {}, {}):
            (
                fulfilled_entitlements_by_course_key,
                unfulfulled_entitlements,
                course_entitlement_available_sessions,
                unfulfilled_entitlement_pseudo_sessions,
            ) = get_entitlements(self.user, None, None)

        assert not fulfilled_entitlements_by_course_key
        assert not unfulfulled_entitlements
        assert not course_entitlement_available_sessions
        assert not unfulfilled_entitlement_pseudo_sessions


class TestGetEmailSettingsInfo(SharedModuleStoreTestCase):
    """Tests for get_email_settings_info"""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    @patch("lms.djangoapps.learner_home.views.is_bulk_email_feature_enabled")
    def test_get_email_settings(self, mock_is_bulk_email_enabled):
        # Given 3 courses where bulk email is enabled for 2 and user has opted out of one
        courses = [CourseFactory.create() for _ in range(3)]
        enrollments = [
            CourseEnrollmentFactory.create(user=self.user, course_id=course.id)
            for course in courses
        ]
        optouts = {Optout.objects.create(user=self.user, course_id=courses[1].id)}
        mock_is_bulk_email_enabled.side_effect = (True, True, False)

        # When I get email settings
        show_email_settings_for, course_optouts = get_email_settings_info(
            self.user, enrollments
        )

        # Then the email settings show for courses where bulk email is enabled
        self.assertSetEqual(
            {course.id for course in courses[0:2]}, show_email_settings_for
        )

        # ... and course optouts are returned
        self.assertSetEqual(
            {optout.course_id for optout in optouts},
            set(course_optouts),
        )


class TestDashboardView(SharedModuleStoreTestCase, APITestCase):
    """Tests for the dashboard view"""

    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Get view URL
        cls.view_url = reverse("learner_home:initialize")

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

    @patch.dict(settings.FEATURES, ENTERPRISE_ENABLED=False)
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
                "emailConfirmation",
                "enterpriseDashboard",
                "platformSettings",
                "courses",
                "suggestedCourses",
            ]
        )

        assert expected_keys == response_data.keys()

    @patch.dict(settings.FEATURES, ENTERPRISE_ENABLED=False)
    @patch("lms.djangoapps.learner_home.views.get_user_account_confirmation_info")
    def test_email_confirmation(self, mock_user_conf_info):
        """Test that email confirmation info passes through correctly"""

        # Given I am logged in
        self.log_in()

        # (and we have tons of mocks to avoid integration tests)
        mock_user_conf_info_response = (
            TestGetUserAccountConfirmationInfo.mock_response()
        )
        mock_user_conf_info.return_value = mock_user_conf_info_response

        # When I request the dashboard
        response = self.client.get(self.view_url)

        # Then I get the expected success response
        assert response.status_code == 200
        response_data = json.loads(response.content)

        self.assertDictEqual(
            response_data["emailConfirmation"],
            {
                "isNeeded": mock_user_conf_info_response["isNeeded"],
                "sendEmailUrl": mock_user_conf_info_response["sendEmailUrl"],
            },
        )

    @patch.dict(settings.FEATURES, ENTERPRISE_ENABLED=False)
    @patch("lms.djangoapps.learner_home.views.cert_info")
    def test_get_cert_statuses(self, mock_get_cert_info):
        """Test that cert information gets loaded correctly"""

        # Given I am logged in
        self.log_in()

        # (and we have tons of mocks to avoid integration tests)
        mock_enrollment = create_test_enrollment(
            self.user, course_mode=CourseMode.VERIFIED
        )
        mock_cert_info = {
            "status": "downloadable",
            "mode": "verified",
            "linked_in_url": None,
            "show_survey_button": False,
            "can_unenroll": True,
            "show_cert_web_view": True,
            "cert_web_view_url": random_url(),
        }
        mock_get_cert_info.return_value = mock_cert_info

        # When I request the dashboard
        response = self.client.get(self.view_url)

        # Then I get the expected success response
        assert response.status_code == 200
        response_data = json.loads(response.content)

        self.assertDictEqual(
            response_data["courses"][0]["certificate"],
            {
                "availableDate": mock_enrollment.course.certificate_available_date,
                "isRestricted": False,
                "isEarned": True,
                "isDownloadable": True,
                "certPreviewUrl": mock_cert_info["cert_web_view_url"],
            },
        )
