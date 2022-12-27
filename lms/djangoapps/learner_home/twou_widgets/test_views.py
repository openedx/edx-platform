"""
Tests for TwoU widget context
"""

import json
from unittest.mock import patch

import ddt
from django.urls import reverse_lazy
from rest_framework.test import APITestCase

from common.djangoapps.student.tests.factories import UserFactory


@ddt.ddt
class TestTwoUWidgetContextView(APITestCase):
    """Tests for the TwoU widget context."""

    password = "test"
    view_url = reverse_lazy("learner_home:twou_widget_context")

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    @ddt.data("US", "")
    @patch("lms.djangoapps.learner_home.twou_widgets.views.country_code_from_ip")
    def test_country_code_from_ip(self, country_code, mock_country_code_from_ip):
        """Test that country code gets populated correctly."""

        mock_country_code_from_ip.return_value = country_code

        # Given I am logged in.
        self.client.login(username=self.user.username, password=self.password)

        # When I request for TwoU widget context.
        response = self.client.get(self.view_url)

        response_data = json.loads(response.content)
        self.assertEqual(response_data["countryCode"], country_code)

    def test_unauthenticated_request(self):
        """
        Test unauthenticated request to TwoU widget context API view.
        """

        # When I request for TwoU widget context without logging in.
        response = self.client.get(self.view_url)
        self.assertEqual(response.status_code, 401)
