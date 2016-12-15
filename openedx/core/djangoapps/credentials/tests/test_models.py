"""Tests for models supporting Credentials-related functionality."""

from django.test import TestCase
from openedx.core.djangoapps.credentials.tests.mixins import CredentialsApiConfigMixin


class TestCredentialsApiConfig(CredentialsApiConfigMixin, TestCase):
    """Tests covering the CredentialsApiConfig model."""
    def test_url_construction(self):
        """Verify that URLs returned by the model are constructed correctly."""
        credentials_config = self.create_credentials_config()

        self.assertEqual(
            credentials_config.internal_api_url,
            credentials_config.internal_service_url.strip('/') + '/api/v1/')

        self.assertEqual(
            credentials_config.public_api_url,
            credentials_config.public_service_url.strip('/') + '/api/v1/')

    def test_is_learner_issuance_enabled(self):
        """
        Verify that the property controlling display on the student dashboard is only True
        when configuration is enabled and all required configuration is provided.
        """
        credentials_config = self.create_credentials_config(enabled=False)
        self.assertFalse(credentials_config.is_learner_issuance_enabled)

        credentials_config = self.create_credentials_config(enable_learner_issuance=False)
        self.assertFalse(credentials_config.is_learner_issuance_enabled)

        credentials_config = self.create_credentials_config()
        self.assertTrue(credentials_config.is_learner_issuance_enabled)

    def test_is_studio_authoring_enabled(self):
        """
        Verify that the property controlling display in the Studio authoring is only True
        when configuration is enabled and all required configuration is provided.
        """
        credentials_config = self.create_credentials_config(enabled=False)
        self.assertFalse(credentials_config.is_studio_authoring_enabled)

        credentials_config = self.create_credentials_config(enable_studio_authoring=False)
        self.assertFalse(credentials_config.is_studio_authoring_enabled)

        credentials_config = self.create_credentials_config()
        self.assertTrue(credentials_config.is_studio_authoring_enabled)
