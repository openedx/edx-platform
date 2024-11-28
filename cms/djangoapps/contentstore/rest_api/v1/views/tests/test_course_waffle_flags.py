"""
Unit tests for the course waffle flags view
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from cms.djangoapps.contentstore.tests.utils import CourseTestCase
from openedx.core.djangoapps.waffle_utils.models import WaffleFlagCourseOverrideModel

User = get_user_model()


class CourseWaffleFlagsViewTest(CourseTestCase):
    """
    Tests for the CourseWaffleFlagsView endpoint, which returns waffle flag states
    for a specific course or globally if no course ID is provided.
    """

    course_waffle_flags = [
        "use_new_custom_pages",
        "use_new_schedule_details_page",
        "use_new_advanced_settings_page",
        "use_new_grading_page",
        "use_new_updates_page",
        "use_new_import_page",
        "use_new_export_page",
        "use_new_files_uploads_page",
        "use_new_video_uploads_page",
        "use_new_course_outline_page",
        "use_new_unit_page",
        "use_new_course_team_page",
        "use_new_certificates_page",
        "use_new_textbooks_page",
        "use_new_group_configurations_page",
    ]

    other_expected_waffle_flags = ["enable_course_optimizer"]

    def setUp(self):
        """
        Set up test data and state before each test method.

        This method initializes the endpoint URL and creates a set of waffle flags
        for the test course, setting each flag's value to `True`.
        """
        super().setUp()
        self.url = reverse("cms.djangoapps.contentstore:v1:course_waffle_flags")
        self.create_waffle_flags(self.course_waffle_flags)
        self.create_custom_waffle_flags()

    def create_custom_waffle_flags(self, enabled=True):
        """
        Helper method to create waffle flags that are not part of `course_waffle_flags` and have
        a different format.
        """
        WaffleFlagCourseOverrideModel.objects.create(
            waffle_flag="contentstore.enable_course_optimizer",
            course_id=self.course.id,
            enabled=enabled,
        )

    def create_waffle_flags(self, flags, enabled=True):
        """
        Helper method to create waffle flag entries in the database for the test course.

        Args:
            flags (list): A list of flag names to set up.
            enabled (bool): The value to set for each flag's enabled state.
        """
        for flag in flags:
            WaffleFlagCourseOverrideModel.objects.create(
                waffle_flag=f"contentstore.new_studio_mfe.{flag}",
                course_id=self.course.id,
                enabled=enabled,
            )

    def expected_response(self, enabled=False):
        """
        Generate an expected response dictionary based on the enabled flag.

        Args:
            enabled (bool): State to assign to each waffle flag in the response.

        Returns:
            dict: A dictionary with each flag set to the value of `enabled`.
        """
        res = {flag: enabled for flag in self.course_waffle_flags}
        for flag in self.other_expected_waffle_flags:
            res[flag] = enabled
        return res

    def test_get_course_waffle_flags_with_course_id(self):
        """
        Test that waffle flags for a specific course are correctly returned when
        a valid course ID is provided.

        Expected Behavior:
        - The response should return HTTP 200 status.
        - Each flag returned should be `True` as set up in the `setUp` method.
        """
        course_url = reverse(
            "cms.djangoapps.contentstore:v1:course_waffle_flags",
            kwargs={"course_id": self.course.id},
        )

        expected_response = self.expected_response(enabled=True)
        expected_response["use_new_home_page"] = False

        response = self.client.get(course_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(expected_response, response.data)

    def test_get_course_waffle_flags_without_course_id(self):
        """
        Test that the default waffle flag states are returned when no course ID is provided.

        Expected Behavior:
        - The response should return HTTP 200 status.
        - Each flag returned should default to `False`, representing the global
          default state for each flag.
        """
        expected_response = self.expected_response(enabled=False)
        expected_response["use_new_home_page"] = False

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(expected_response, response.data)
