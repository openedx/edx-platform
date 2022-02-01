"""
Tests for the course advanced settings API.
"""
import json

import ddt
from django.test import override_settings
from django.urls import reverse
from milestones.tests.utils import MilestonesTestCaseMixin

from cms.djangoapps.contentstore.tests.utils import CourseTestCase


@ddt.ddt
class CourseAdvanceSettingViewTest(CourseTestCase, MilestonesTestCaseMixin):
    """
    Tests for AdvanceSettings API View.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "cms.djangoapps.contentstore:v0:course_advanced_settings",
            kwargs={"course_id": self.course.id},
        )

    def get_and_check_developer_response(self, response):
        """
        Make basic asserting about the presence of an error response, and return the developer response.
        """
        content = json.loads(response.content.decode("utf-8"))
        assert "developer_message" in content
        return content["developer_message"]

    def test_permissions_unauthenticated(self):
        """
        Test that an error is returned in the absence of auth credentials.
        """
        self.client.logout()
        response = self.client.get(self.url)
        error = self.get_and_check_developer_response(response)
        assert error == "Authentication credentials were not provided."

    def test_permissions_unauthorized(self):
        """
        Test that an error is returned if the user is unauthorised.
        """
        client, _ = self.create_non_staff_authed_user_client()
        response = client.get(self.url)
        error = self.get_and_check_developer_response(response)
        assert error == "You do not have permission to perform this action."

    @ddt.data(
        ("ENABLE_EDXNOTES", "edxnotes"),
        ("ENABLE_OTHER_COURSE_SETTINGS", "other_course_settings"),
    )
    @ddt.unpack
    def test_conditionally_excluded_fields_present(self, setting, excluded_field):
        """
        Test that the response contain all fields irrespective of exclusions.
        """
        for setting_value in (True, False):
            with override_settings(FEATURES={setting: setting_value}):
                response = self.client.get(self.url)
                content = json.loads(response.content.decode("utf-8"))
                assert excluded_field in content

    @ddt.data(
        ("", ("display_name", "due"), ()),
        ("display_name", ("display_name",), ("due", "edxnotes")),
        ("display_name,edxnotes", ("display_name", "edxnotes"), ("due", "tags")),
    )
    @ddt.unpack
    def test_filtered_fields(self, filtered_fields, present_fields, absent_fields):
        """
        Test that the response contain all fields that are in the filter, and none that are filtered out.
        """
        response = self.client.get(self.url, {"filter_fields": filtered_fields})
        content = json.loads(response.content.decode("utf-8"))
        for field in present_fields:
            assert field in content.keys()
        for field in absent_fields:
            assert field not in content.keys()
