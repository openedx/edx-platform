"""
Common mixins for module.
"""
import json
from unittest.mock import patch

from rest_framework import status


class PermissionAccessMixin:
    """
    Mixin for testing permission access for views.
    """

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
        self.assertEqual(error, "Authentication credentials were not provided.")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch.dict('django.conf.settings.FEATURES', {'DISABLE_ADVANCED_SETTINGS': True})
    def test_permissions_unauthorized(self):
        """
        Test that an error is returned if the user is unauthorised.
        """
        client, _ = self.create_non_staff_authed_user_client()
        response = client.get(self.url)
        error = self.get_and_check_developer_response(response)
        self.assertEqual(error, "You do not have permission to perform this action.")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
