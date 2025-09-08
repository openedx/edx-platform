"""
Unit tests for MobileConfigurationView API endpoint.
"""
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from lms.djangoapps.mobile_api.models import MobileConfig


class MobileConfigurationViewTest(APITestCase):
    """
    Test cases for MobileConfigurationView API endpoint.
    """

    def setUp(self):
        """
        Set up test data and common test utilities.
        """
        self.url = reverse('mobile-configurations', kwargs={'api_version': 'v1'})

    def test_get_mobile_configurations_empty_database(self):
        """
        Test API response when no configurations exist in database.
        """
        # Act
        response = self.client.get(self.url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = {"iap_configs": {}}
        self.assertEqual(response.data, expected_data)

    def test_get_mobile_configurations_with_regular_configs(self):
        """
        Test API response with regular (non-IAP) configurations.
        """
        # Arrange
        MobileConfig.objects.create(name='app_version', value='2.1.0')
        MobileConfig.objects.create(name='enable_dark_mode', value='true')
        MobileConfig.objects.create(name='api_timeout', value='30')

        # Act
        response = self.client.get(self.url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = {
            "iap_configs": {},
            "app_version": "2.1.0",
            "enable_dark_mode": "true",
            "api_timeout": "30"
        }
        self.assertEqual(response.data, expected_data)
