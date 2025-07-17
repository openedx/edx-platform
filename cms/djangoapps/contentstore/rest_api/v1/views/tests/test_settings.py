"""
Unit tests for course settings views.
"""
from unittest.mock import patch

import ddt
from django.conf import settings
from django.urls import reverse
from rest_framework import status

from cms.djangoapps.contentstore.tests.utils import CourseTestCase
from cms.djangoapps.contentstore.utils import get_proctored_exam_settings_url
from common.djangoapps.util.course import get_link_for_about_page
from openedx.core.djangoapps.credit.tests.factories import CreditCourseFactory

from ...mixins import PermissionAccessMixin


@ddt.ddt
class CourseSettingsViewTest(CourseTestCase, PermissionAccessMixin):
    """
    Tests for CourseSettingsView.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "cms.djangoapps.contentstore:v1:course_settings",
            kwargs={"course_id": self.course.id},
        )

    def test_course_settings_response(self):
        """Check successful response content"""
        response = self.client.get(self.url)
        expected_response = {
            "about_page_editable": True,
            "can_show_certificate_available_date_field": False,
            "course_display_name": self.course.display_name,
            "course_display_name_with_default": self.course.display_name_with_default,
            "credit_eligibility_enabled": True,
            "enrollment_end_editable": True,
            "enable_extended_course_details": False,
            "is_credit_course": False,
            "is_entrance_exams_enabled": True,
            "is_prerequisite_courses_enabled": False,
            "language_options": settings.ALL_LANGUAGES,
            "lms_link_for_about_page": get_link_for_about_page(self.course),
            "marketing_enabled": False,
            "mfe_proctored_exam_settings_url": get_proctored_exam_settings_url(
                self.course.id
            ),
            "platform_name": settings.PLATFORM_NAME,
            "short_description_editable": True,
            "sidebar_html_enabled": False,
            "show_min_grade_warning": False,
            "upgrade_deadline": None,
            "licensing_enabled": False,
        }

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(expected_response, response.data)

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_CREDIT_ELIGIBILITY": True})
    def test_credit_eligibility_setting(self):
        """
        Make sure if the feature flag is enabled we have updated the dict keys in response.
        """
        _ = CreditCourseFactory(course_key=self.course.id, enabled=True)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("credit_requirements", response.data)
        self.assertTrue(response.data["is_credit_course"])

    @patch.dict(
        "django.conf.settings.FEATURES",
        {
            "ENABLE_PREREQUISITE_COURSES": True,
            "MILESTONES_APP": True,
        },
    )
    def test_prerequisite_courses_enabled_setting(self):
        """
        Make sure if the feature flags are enabled we have updated the dict keys in response.
        """
        response = self.client.get(self.url)
        self.assertIn("possible_pre_requisite_courses", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
