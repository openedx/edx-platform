"""Tests for serializers for the Learner Home"""

from django.test import TestCase

from lms.djangoapps.learner_home.twou_widgets.serializers import (
    TwoUWidgetContextSerializer,
)


class TestTwoUWidgetContextSerializer(TestCase):
    """High-level tests for TwoUWidgetContextSerializer"""

    def test_empty(self):
        """Test that empty input returns the right output"""

        output_data = TwoUWidgetContextSerializer(
            {
                "countryCode": "",
            }
        ).data

        self.assertDictEqual(
            output_data,
            {
                "countryCode": "",
            },
        )

    def test_happy_path(self):
        """Test that data serializes correctly"""

        output_data = TwoUWidgetContextSerializer(
            {
                "countryCode": "US",
            }
        ).data

        self.assertDictEqual(
            output_data,
            {
                "countryCode": "US",
            },
        )
