"""Tests for serializers for the MFE Context"""

from django.test import TestCase

from openedx.core.djangoapps.user_authn.api.tests.test_data import (
    mock_mfe_context_data,
    expected_mfe_context_data,
    mock_default_mfe_context_data,
    default_expected_mfe_context_data,
)
from openedx.core.djangoapps.user_authn.serializers import MFEContextSerializer


class TestMFEContextSerializer(TestCase):
    """
    High-level unit tests for MFEContextSerializer
    """

    def test_mfe_context_serializer(self):
        """
        Test MFEContextSerializer with mock data that serializes data correctly
        """

        output_data = MFEContextSerializer(
            mock_mfe_context_data
        ).data

        self.assertDictEqual(
            output_data,
            expected_mfe_context_data
        )

    def test_mfe_context_serializer_default_response(self):
        """
        Test MFEContextSerializer with default data
        """
        serialized_data = MFEContextSerializer(
            mock_default_mfe_context_data
        ).data

        self.assertDictEqual(
            serialized_data,
            default_expected_mfe_context_data
        )
