"""
Tests for the course advanced settings API.
"""
import json
from unittest.mock import patch

import ddt
from django.test import override_settings
from django.urls import reverse
from milestones.tests.utils import MilestonesTestCaseMixin
from rest_framework.exceptions import ValidationError

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

    @ddt.data(
        ("ENABLE_EDXNOTES", "edxnotes"),
        ("ENABLE_OTHER_COURSE_SETTINGS", "other_course_settings"),
    )
    @ddt.unpack
    def test_disabled_fetch_all_query_param(self, setting, excluded_field):
        with override_settings(FEATURES={setting: False}):
            resp = self.client.get(self.url, {"fetch_all": 0})
            assert excluded_field not in resp.data

    @patch('cms.djangoapps.contentstore.rest_api.v0.views.advanced_settings.set_course_app_status')
    def test_patch_multiple_advanced_settings(self, mock_set_course_app_status):
        """
        Test that updating multiple advanced settings calls set_course_app_status for corresponding apps.
        """
        with override_settings(FEATURES={"ENABLE_EDXNOTES": True}):
            mock_set_course_app_status.return_value = True

            # Test updating both calculator and edxnotes settings
            data = {
                "show_calculator": {
                    "value": True
                },
                "edxnotes": {
                    "value": True
                },
                "other_setting": {
                    "value": "some_value"
                }
            }
            response = self.client.patch(self.url, json.dumps(data), content_type="application/json")

            assert mock_set_course_app_status.call_count == 2
            calls = mock_set_course_app_status.call_args_list
            actual_calls = [call.kwargs for call in calls]

            # Extract the calls without the request object for easier comparison
            actual_calls = [
                {
                    'course_key': call_kwargs['course_key'],
                    'app_id': call_kwargs['app_id'],
                    'enabled': call_kwargs['enabled']
                }
                for call_kwargs in actual_calls
            ]

            expected_calls = [
                {
                    'course_key': self.course.id,
                    'app_id': 'calculator',
                    'enabled': True
                },
                {
                    'course_key': self.course.id,
                    'app_id': 'edxnotes',
                    'enabled': True
                }
            ]

            # Check that both expected calls were made (order may vary)
            for expected_call in expected_calls:
                assert expected_call in actual_calls

            assert response.status_code == 200

    @patch('cms.djangoapps.contentstore.rest_api.v0.views.advanced_settings.set_course_app_status')
    def test_patch_advanced_setting_with_exception(self, mock_set_course_app_status):
        """
        Test that exceptions in set_course_app_status are caught and don't break the flow.
        """
        # Mock set_course_app_status to raise an exception
        mock_set_course_app_status.side_effect = ValidationError("Course app error")

        data = {
            "show_calculator": {
                "value": True
            },
            "display_name": {
                "value": "Updated Course Name"
            }
        }
        response = self.client.patch(self.url, json.dumps(data), content_type="application/json")

        mock_set_course_app_status.assert_called_once()
        # Check the call arguments (excluding request for easier comparison)
        call_args = mock_set_course_app_status.call_args.kwargs
        expected_args = {
            'course_key': self.course.id,
            'app_id': 'calculator',
            'enabled': True
        }

        for key, expected_value in expected_args.items():
            assert call_args[key] == expected_value

        # Verify the request still succeeds and other settings are processed
        assert response.status_code == 200

    @patch('cms.djangoapps.contentstore.rest_api.v0.views.advanced_settings.set_course_app_status')
    def test_patch_non_advanced_setting_skips_app_status_update(self, mock_set_course_app_status):
        """
        Test that updating non-course app settings doesn't call set_course_app_status.
        """
        data = {
            "display_name": {
                "value": "Updated Course Name"
            },
            "start": {
                "value": "2024-01-01T00:00:00Z"
            }
        }
        response = self.client.patch(self.url, json.dumps(data), content_type="application/json")

        # Verify set_course_app_status was not called
        mock_set_course_app_status.assert_not_called()
        assert response.status_code == 200

    @patch('cms.djangoapps.contentstore.rest_api.v0.views.advanced_settings.set_course_app_status')
    def test_patch_advanced_setting_with_none_value(self, mock_set_course_app_status):
        """
        Test that course app settings with None values don't call set_course_app_status.
        """
        data = {
            "show_calculator": {
                "value": None
            }
        }
        response = self.client.patch(self.url, json.dumps(data), content_type="application/json")

        # Verify set_course_app_status was not called when value is None
        mock_set_course_app_status.assert_not_called()
        assert response.status_code == 200
